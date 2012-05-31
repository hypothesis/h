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

    this

  _setupWrapper: ->
    super
    @wrapper.on 'click', (event) =>
      this.hideSidebar() unless @selectedRanges?.length
    this

  _setupSidebar: ->
    # Create a sidebar if one does not exist. This is a singleton element --
    # even if multiple instances of the app are loaded on a page (some day).
    if not @sidebar?
      sidebar = $(Handlebars.templates.sidebar())
      Annotator.prototype.sidebar = sidebar
      @sidebar = sidebar
      @sidebar.addClass('collapse')
      @sidebar.on 'click', (event) =>  event.stopPropagation()
    this

  _setupHeatmap: () ->
    # Pull the heatmap into the sidebar
    @heatmap = @plugins.Heatmap
    d3.select(@heatmap.element.get(0)).on('click', this.onHeatmapClick)
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
    .on('hide', this.onEditorHide)
    .on('save', this.onEditorSubmit)
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

  onHeatmapClick: () =>
    [x, y] = d3.mouse(d3.event.target)
    target = d3.bisect(@heatmap.index, y)-1
    annotations = @heatmap.buckets[target]
    this.showViewer(annotations) if annotations?.length

  showViewer: (annotations=[], detail=false) ->
    @editor.hide()
    viewer = d3.select(@viewer.element.get(0))

    messages = annotations.map (a) ->
      m = mail.message(null, a.id, a.thread?.split('/') or [])
      m.annotation = a
      m

    root = mail.messageThread().thread(messages)
    context = viewer.datum(root)

    excerpts = context.select('.annotator-listing').selectAll('.hyp-excerpt')
      .data ( -> if detail then root.children else []), (c) -> c.message.id

    if not detail
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
    else
      excerpts.enter()
        .insert('li', '.hyp-annotation').classed('hyp-widget', true)
        .append('div').classed('hyp-excerpt', true)
      excerpts.exit().remove()
      excerpts.select('div.hyp-excerpt').text((d) -> d.message.annotation.quote)

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

          .on 'mouseover', =>
            d3.event.stopPropagation()
            d3.select(d3.event.currentTarget).select('.annotator-controls')
              .transition()
                .style('display', '')
                .style('opacity', 1)

          .on 'mouseout', =>
            d3.event.stopPropagation()
            d3.select(d3.event.currentTarget).select('.annotator-controls')
              .transition()
                .style('display', 'none')
                .style('opacity', 1e-6)

          .on 'click', =>
            event = d3.event
            target = event.target
            unless target instanceof HTMLAnchorElement then return
            event.stopPropagation()

            switch d3.event.target.getAttribute('href')
              when '#reply'
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

          .select('.annotator-controls')
            .style('display', 'none')
            .style('opacity', 1e-6)

        context = items

    @viewer.show()
    this.showSidebar()

  showEditor: (annotation) =>
    unless @plugins.Permissions?.user
      alert("Not logged in!")
      return

    @viewer.hide()
    @editor.load(annotation)

    item = $('<li class="hyp-widget hyp-writer">')
    item.append($(Handlebars.templates.editor(annotation)))
    @editor.element.find('.annotator-listing').empty().append(item)

    d3.select(@viewer.element.get(0)).datum(null)
    this.showSidebar()

  showSidebar: =>
    $(document.documentElement).addClass('hyp-collapse')
    @sidebar.removeClass('collapse')

  hideSidebar: =>
    @sidebar.addClass('collapse')
    $(document.documentElement).removeClass('hyp-collapse')

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
