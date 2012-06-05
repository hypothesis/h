class Hypothesis extends Annotator
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  pluginConfig:
    Heatmap: {}
    Permissions:
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')
    Store:
      loadFromSearch: document.location.href
      annotationData: document.location.href
    Unsupported: {}

  # The last bucket of annotations shown
  @bucket = null

  # Whether the detail view is shown
  @detail = false

  constructor: (element, options) ->
    super

    # Load plugins
    $.extend @pluginConfig, options
    for own name, opts of @pluginConfig
      if not @plugins[name]
        this.addPlugin name, opts

    # Set up interface elements
    this._setupHeatmap()._setupSidebar()

    @heatmap.element.appendTo(@sidebar)
    @viewer.element.appendTo(@sidebar)
    @editor.element.appendTo(@sidebar)
    @sidebar.prependTo(@wrapper)

    @plugins.Auth.withToken (token) =>
      @plugins.Permissions.setUser token.userId

    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      annotation.created = annotation.updated = (new Date()).toString()
      annotation.user = @plugins.Permissions.options.userId(
        @plugins.Permissions.user)

    this

  _setupWrapper: ->
    super
    @wrapper.on 'click', (event) =>
      if @bucket and @detail
        this.showViewer(@bucket)
      else
        this.hideSidebar() unless @selectedRanges?.length
    this

  _setupSidebar: ->
    # Create a sidebar if one does not exist. This is a singleton element --
    # even if multiple instances of the app are loaded on a page (some day).
    if not @sidebar?
      sidebar = $(Handlebars.templates.sidebar())
      Annotator.prototype.sidebar = sidebar
      @sidebar = sidebar
      @sidebar.addClass('hyp-collapsed')
      @sidebar.on 'click', (event) =>  event.stopPropagation()
    this

  _setupHeatmap: () ->
    # Pull the heatmap into the sidebar
    @heatmap = @plugins.Heatmap

    bucket = []

    d3.select(@heatmap.element.get(0))
    .on 'mousemove', =>
      [x, y] = d3.mouse(d3.event.target)
      target = d3.bisect(@heatmap.index, y)-1
      for a in bucket
        d3.selectAll(a.highlights).classed('hyp-active', false)
      bucket = @heatmap.buckets[target] or []
      for a in bucket
        d3.selectAll(a.highlights).classed('hyp-active', true)
    .on 'mouseout', =>
      for a in bucket
        d3.selectAll(a.highlights).classed('hyp-active', false)
    .on 'click', =>
      this.showViewer(bucket) if bucket?.length
    this

  # Creates an instance of Annotator.Viewer and assigns it to the @viewer
  # property, appends it to the @wrapper and sets up event listeners.
  #
  # Returns itself to allow chaining.
  _setupViewer: ->
    @viewer = new Annotator.Viewer(readOnly: @options.readOnly)
    @viewer.hide()
    .on("edit", this.onEditAnnotation)
    .on("delete", this.onDeleteAnnotation)

    this.subscribe 'annotationCreated', (annotation) =>
      this.updateViewer [annotation]

    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = this._createEditor()
    @editor.on 'hide', () =>
      if not d3.select(@viewer.element.get(0)).datum()
        this.hideSidebar()
    this

  _createEditor: ->
    editor = new Annotator.Editor()
    editor.hide()
    # TODO: this is ugly... we shouldn't need to do this in both clauses --
    # Annotator should handle highlights better
    .on('hide', =>
      if editor.annotation?.highlights? and not editor.annotation.ranges?
        for h in editor.annotation.highlights
          $(h).replaceWith(h.childNodes)
      this.onEditorHide()
    )
    .on('save', (annotation) =>
      if annotation?.highlights?
        for h in annotation.highlights
          $(h).replaceWith(h.childNodes)
      this.onEditorSubmit(annotation)
    )
    editor.fields = [{
      element: editor.element,
      load: (field, annotation) ->
        $(field).find('textarea').val(annotation.text || '')
      submit: (field, annotation) ->
        annotation.text = $(field).find('textarea').val()
    }]

    # Patch the editor, taking out the controls which will be added via
    # Handlebars as part of the editor template.
    editor.element.find('.annotator-controls').remove()

    editor

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    $(document).bind({
      "mouseup":   this.checkForEndSelection
    })
    this

  # Public: Initialises an annotation either from an object representation or
  # an annotation created with Annotator#createAnnotation(). It finds the
  # selected range and higlights the selection in the DOM.
  #
  # annotation - An annotation Object to initialise.
  # fireEvents - Will fire the 'annotationCreated' event if true.
  #
  # Examples
  #
  #   # Create a brand new annotation from the currently selected text.
  #   annotation = annotator.createAnnotation()
  #   annotation = annotator.setupAnnotation(annotation)
  #   # annotation has now been assigned the currently selected range
  #   # and a highlight appended to the DOM.
  #
  #   # Add an existing annotation that has been stored elsewere to the DOM.
  #   annotation = getStoredAnnotationWithSerializedRanges()
  #   annotation = annotator.setupAnnotation(annotation)
  #
  # Returns the initialised annotation.
  setupAnnotation: (annotation, args...) ->
    # Delagate to Annotator implementation after we give it a valid array of
    # ranges
    if annotation.thread
      annotation.ranges = annotation.ranges or []
    super annotation, args...

  showViewer: (annotations=[], detail=false) ->
    viewer = d3.select(@viewer.element.get(0))

    # Thread the messages using JWZ
    messages = annotations.map (a) ->
      m = mail.message(null, a.id, a.thread?.split('/') or [])
      m.annotation = a
      m

    root = mail.messageThread().thread(messages)
    context = viewer.datum(root)

    # Bind the excerpt data so the excerpt can be removed in the bucket view
    # or updated and rendered in the detail view.
    excerpts = context.select('.annotator-listing').selectAll('.hyp-excerpt')
      .data ( -> if detail then root.children else []), (c) -> c.message.id

    if not detail
      # Save the state so the bucket view can be restored when exiting
      # the detail view.
      @bucket = annotations
      @detail = false

      # Remove the excerpts
      excerpts.exit().remove()

      context = context.select('.annotator-listing')
      context.select('.annotator-listing > li.hyp-excerpt').remove()
      items = context.selectAll('.annotator-listing > li.hyp-annotation')
        .data ((c) -> c.children), ((c) -> c.message.id)
      items.enter().append('li')
        .classed('hyp-annotation', true)
      items.exit().remove()
      items
        .html((d, i) => Handlebars.templates.summary(d.message.annotation))
        .classed('hyp-detail', false)
        .classed('hyp-summary', true)
        .classed('hyp-widget', true)
        .on 'click', (d, i) =>
          a = d.message.annotation
          query =
            thread: if a.thread then [a.thread, a.id].join('/') else a.id
          @plugins.Store._apiRequest 'search', query, (data) =>
            if data?.rows then this.updateViewer(data.rows || [])
          this.showViewer([a], true)
        .on 'mouseover', =>
          d3.event.stopPropagation()
          item = d3.select(d3.event.currentTarget).datum().message.annotation
          d3.selectAll(item.highlights).classed('hyp-active', true)
        .on 'mouseout', =>
          d3.event.stopPropagation()
          item = d3.select(d3.event.currentTarget).datum().message.annotation
          d3.selectAll(item.highlights).classed('hyp-active', false)
    else
      # Mark that the detail view is now shown, so that exiting returns to the
      # bucket view rather than the document.
      @detail = true

      excerpts.enter()
        .insert('li', '.hyp-annotation')
          .classed('hyp-widget', true)
          .classed('hyp-excerpt', true)
        .append('div')
      excerpts.exit().remove()
      excerpts.select('div').text((d) -> d.message.annotation.quote)

      loop
        context = context.select('.annotator-listing')
        items = context.selectAll('.annotator-listing > li.hyp-annotation')
          .data ((c) -> c.children), ((c) -> c.message.id)
        break unless items.length

        items.enter().append('li').classed('hyp-annotation', true)
        items.exit().remove()
        items
          .html((d, i) => Handlebars.templates.detail(d.message.annotation))
          .classed('hyp-widget', (c) -> not c.parent.message?)
          .classed('hyp-detail', true)
          .classed('hyp-summary', false)

          .sort (d, e) =>
            n = d.message.annotation.created
            m = e.message.annotation.created
            (n < m) - (m < n)

          .on 'mouseover', =>
            d3.event.stopPropagation()
            d3.select(d3.event.currentTarget).classed('hyp-hover', true)

          .on 'mouseout', =>
            d3.event.stopPropagation()
            d3.select(d3.event.currentTarget).classed('hyp-hover', false)

          .on 'click', =>
            event = d3.event
            target = event.target
            unless target instanceof HTMLAnchorElement then return
            event.stopPropagation()

            switch d3.event.target.getAttribute('href')
              when '#collapse'
                d3.event.preventDefault()
                parent = d3.select(event.currentTarget)
                parent.classed('hyp-collapsed', !parent.classed('hyp-collapsed'))

              when '#reply'
                d3.event.preventDefault()
                parent = d3.select(event.currentTarget).datum()
                reply = this.createAnnotation()
                reply.thread = this.threadId(parent.message.annotation)

                editor = this._createEditor()
                editor.load(reply)
                editor.element.removeClass('annotator-outer')

                item = d3.select(d3.event.currentTarget)
                  .select('.annotator-listing')
                  .insert('li', 'li')
                    .classed('hyp-writer', true)

                editor.element.appendTo(item.node())

                item.select('.annotator-listing')
                  .selectAll('li')
                    .data([reply])
                    .enter().append('li')
                      .html(Handlebars.templates.editor)
                      .on 'mouseover', => d3.event.stopPropagation()

                editor.on('hide', => item.remove())

        context = items

    @editor.hide()
    @viewer.show()
    this.showSidebar()

  showEditor: (annotation) =>
    unless @plugins.Permissions?.user
      alert("Not logged in!")
      return

    @viewer.hide()
    @editor.load(annotation)

    this.setupAnnotation(annotation, false)
    delete annotation.ranges

    excerpt = $('<li class="hyp-widget hyp-excerpt">')
    excerpt.append($("<div>#{annotation.quote}</div>"))

    item = $('<li class="hyp-widget hyp-writer">')
    item.append($(Handlebars.templates.editor(annotation)))

    @editor.element.find('.annotator-listing').empty()
      .append(excerpt)
      .append(item)

    d3.select(@viewer.element.get(0)).datum(null)
    this.showSidebar()

  showSidebar: =>
    @sidebar.removeClass('hyp-collapsed')

  hideSidebar: =>
    @sidebar.addClass('hyp-collapsed')

  updateViewer: (annotations) =>
    existing = d3.select(@viewer.element.get(0)).datum()
    if existing?
      annotations = existing.flattenChildren()?.map((c) -> c.annotation)
        .concat(annotations)
    this.showViewer(annotations or [], true)

  threadId: (annotation) ->
    if annotation?.thread?
      annotation.thread + '/' + annotation.id
    else
      annotation.id
