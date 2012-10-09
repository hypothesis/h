class Hypothesis extends Annotator
  # Annotator state variables.
  this::bucket = -1     # * The index of the bucket shown in the summary view
  this::detail = false  # * Whether the viewer shows a summary or detail listing
  this::hash = -1       # * cheap UUID :cake:
  this::cache = {}      # * object cache
  this::visible = false # * Whether the sidebar is visible

  # Plugin configuration
  options:
    Heatmap: {}
    Permissions:
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')

  constructor: (element, options) ->
    # Establish cross-domain communication to the widget host
    @provider = new easyXDM.Rpc
      swf: options.swf
      onReady: this._initialize
    ,
      local:
        publish: (event, args, k, fk) =>
          if event in ['annotationCreated']
            [h] = args
            annotation = @cache[h]
            this.publish event, [annotation]
        addPlugin: => this.addPlugin arguments...
        createAnnotation: =>
          @cache[h = ++@hash] = this.createAnnotation()
          h
        showEditor: (stub) =>
          h = stub.hash
          annotation = $.extend @cache[h], stub,
            hash:
              toJSON: => undefined
              valueOf: => h
          if @plugins.Permissions.user?
            this.showEditor annotation
          else
            showAuth true
            @editor.hide()
            this.show()
        # This guy does stuff when you "back out" of the interface. 
        # (Currently triggered by a click on the source page.)
        back: =>
          # If it's in the detail view, loads the bucket back up.
          if @detail
            this.showViewer(@heatmap.buckets[@bucket])
            this.publish('hostUpdated')
          # If it's not in the detail view, the assumption is that it's in the
          # bucket view and hides the whole interface.
          else
            this.hide()
        update: => this.publish 'hostUpdated'
      remote:
        publish: {}
        setupAnnotation: {}
        onEditorHide: {}
        onEditorSubmit: {}
        showFrame: {}
        hideFrame: {}
        getHighlights: {}
        setActiveHighlights: {}
        getMaxBottom: {}
        scrollTop: {}

    super

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    this

  _initialize: =>
    # Set up interface elements
    this._setupHeatmap()
    @wrapper.append(@viewer.element, @editor.element)
    @heatmap.element.appendTo(document.body)
    @viewer.show()

    @provider.getMaxBottom (max) =>
      $('#toolbar').css("top", "#{max}px")
      $('#gutter').css("padding-top", "#{max}px")
      @heatmap.BUCKET_THRESHOLD_PAD = (
        max + @heatmap.constructor.prototype.BUCKET_THRESHOLD_PAD
      )

    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      annotation.created = annotation.updated = (new Date()).toString()
      annotation.user = @plugins.Permissions.options.userId(
        @plugins.Permissions.user)

    this.publish 'hostUpdated'

  _setupWrapper: ->
    @wrapper = $('#wrapper')
    .on 'mousewheel', (event, delta) ->
      # prevent overscroll from scrolling host frame
      # http://stackoverflow.com/questions/5802467
      scrollTop = $(this).scrollTop()
      scrollBottom = $(this).get(0).scrollHeight - $(this).innerHeight()
      if delta > 0 and scrollTop == 0
        event.preventDefault()
      else if delta < 0 and scrollTop == scrollBottom
        event.preventDefault()
    this

  _setupDocumentEvents: ->
    $('#toolbar .tri').click =>
      if @visible
        this.hide()
      else
        if @viewer.isShown() and @bucket == -1
          this._fillDynamicBucket()
        this.show()
    this

  _setupDynamicStyle: ->
    this

  _setupHeatmap: () ->
    @heatmap = @plugins.Heatmap

    # Update the heatmap when certain events are pubished
    events = [
      'annotationCreated'
      'annotationDeleted'
      'annotationsLoaded'
      'hostUpdated'
    ]

    for event in events
      this.subscribe event, =>
        @provider.getHighlights ({highlights, offset}) =>
          @heatmap.updateHeatmap
            highlights: highlights.map (hl) =>
              hl.data = @cache[hl.data]
              hl
            offset: offset
          if @visible and @viewer.isShown() and @bucket == -1 and not @detail
            this._fillDynamicBucket()

    @heatmap.element.click =>
      @bucket = -1
      this._fillDynamicBucket()
      this.show()

    @heatmap.subscribe 'updated', =>
      tabs = d3.select(document.body)
        .selectAll('div.hyp-heatmap-tab')
        .data =>
          buckets = []
          @heatmap.index.forEach (b, i) =>
            if @heatmap.buckets[i].length > 0
              buckets.push i
            else if @heatmap.isUpper(i) or @heatmap.isLower(i)
              buckets.push i
          buckets

      {highlights, offset} = d3.select(@heatmap.element[0]).datum()
      height = $(window).outerHeight(true)
      pad = height * .2

      # Enters into tabs var, and generates bucket pointers from them
      tabs.enter().append('div')
        .classed('hyp-heatmap-tab', true)

      tabs.exit().remove()

      tabs

        .style 'top', (d) =>
          "#{(@heatmap.index[d] + @heatmap.index[d+1]) / 2}px"

        .html (d) =>
          "<div class='label'>#{@heatmap.buckets[d].length}</div><div class='svg'></div>"

        .classed('upper', @heatmap.isUpper)
        .classed('lower', @heatmap.isLower)

        # Creates highlights corresponding bucket when mouse is hovered
        .on 'mousemove', (bucket) =>
          unless @viewer.isShown() and @detail
            unless @heatmap.buckets[bucket]?.length then bucket = @bucket
            @provider.setActiveHighlights @heatmap.buckets[bucket]?.map (a) =>
              a.hash.valueOf()

        # Gets rid of them after
        .on 'mouseout', =>
          unless @viewer.isShown() and @detail
            @provider.setActiveHighlights @heatmap.buckets[@bucket]?.map (a) =>
              a.hash.valueOf()

        # Does one of a few things when a tab is clicked depending on type
        .on 'mouseup', (bucket) =>
          d3.event.preventDefault()

          # If it's the upper tab, scroll to next bucket above
          if @heatmap.isUpper bucket
            threshold = offset + @heatmap.index[0]
            next = highlights.reduce (next, hl) ->
              if next < hl.offset.top < threshold then hl.offset.top else next
            , threshold - height
            @provider.scrollTop next - pad
            @bucket = -1
            this._fillDynamicBucket()

          # If it's the lower tab, scroll to next bucket below
          else if @heatmap.isLower bucket
            threshold = offset + @heatmap.index[0] + pad
            next = highlights.reduce (next, hl) ->
              if threshold < hl.offset.top < next then hl.offset.top else next
            , offset + height
            @provider.scrollTop next - pad
            @bucket = -1
            this._fillDynamicBucket()

          # If it's neither of the above, load the bucket into the viewer
          else
            annotations = @heatmap.buckets[bucket]
            @bucket = bucket
            this.showViewer(annotations)
            this.show()

          tabs.classed('flip', (d) => @bucket == d)

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

    # Show newly created annotations in the viewer immediately
    this.subscribe 'annotationCreated', (annotation) =>
      this.updateViewer [annotation]

    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = this._createEditor()
    .on('hide', @provider.onEditorHide)
    .on('save', @provider.onEditorSubmit)
    this

  _createEditor: ->
    editor = new Annotator.Editor()
    editor.hide()
    editor.fields = [{
      element: editor.element,
      load: (field, annotation) ->
        $(field).find('textarea').val(annotation.text || '')
      submit: (field, annotation) ->
        annotation.text = $(field).find('textarea').val()
    }]

    editor

  _fillDynamicBucket: ->
    {highlights, offset} = d3.select(@heatmap.element[0]).datum()
    bottom = offset + @heatmap.element.height()
    this.showViewer highlights.reduce (acc, hl) =>
      if hl.offset.top >= offset and hl.offset.top <= bottom
        acc.push hl.data
      acc
    , []

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
  setupAnnotation: (annotation) ->
    # Delagate to Annotator implementation after we give it a valid array of
    # ranges. This is needed until Annotator stops assuming ranges need to be
    # added.
    if annotation.thread
      annotation.ranges = []

    if not annotation.hash
      @cache[h = ++@hash] = $.extend annotation,
        hash:
          toJSON: => undefined
          valueOf: => h
    stub =
      hash: annotation.hash.valueOf()
      ranges: annotation.ranges
    @provider.setupAnnotation stub

  showViewer: (annotations=[], detail=false) =>
    # Thread the messages using JWZ
    messages = mail.messageThread().thread annotations.map (a) ->
      m = mail.message(null, a.id, a.thread?.split('/') or [])
      m.annotation = a
      m

    thread = (context, selector) ->
      context.select('.annotator-listing')
        .selectAll(-> d3.selectAll(this.children).filter(selector)[0])
        .data ((m) -> m.children), ((d) -> d.message.id)

    context = d3.select(@viewer.element[0]).datum(messages)
    items = thread context, '.hyp-annotation'
    excerpts = thread context, '.hyp-excerpt'

    if not detail
      # Save the state so the bucket view can be restored when exiting
      # the detail view.
      @detail = false

      excerpts.remove()
      excerpts.exit().remove()

      items.enter().append('li').classed('hyp-annotation', true)
      items.exit().remove()
      items
        .each (d) ->
          _t = d3.select(this)
          unless this and _t.classed('hyp-summary')
            _t.html Handlebars.templates.summary d.message.annotation
        .classed('hyp-detail', false)
        .classed('hyp-summary', true)
        .classed('hyp-paper', true)
        .on 'mouseup', (d, i) =>
          a = d.message.annotation
          query =
            thread: if a.thread then [a.thread, a.id].join('/') else a.id
          @plugins.Store._apiRequest 'search', query, (data) =>
            if data?.rows then this.updateViewer(data.rows || [])
          this.showViewer([a], true)
        .on 'mouseover', =>
          d3.event.stopPropagation()
          item = d3.select(d3.event.currentTarget).datum().message.annotation
          @provider.setActiveHighlights [item.hash.valueOf()]
        .on 'mouseout', =>
          d3.event.stopPropagation()
          item = d3.select(d3.event.currentTarget).datum().message.annotation
          @provider.setActiveHighlights @heatmap.buckets[@bucket]?.map (a) =>
            a.hash.valueOf()
    else
      # Mark that the detail view is now shown, so that exiting returns to the
      # bucket view rather than the document.
      @detail = true

      excerpts.enter()
        .insert('li', '.hyp-annotation')
          .classed('hyp-paper', true)
          .classed('hyp-excerpt', true)
        .append('blockquote')
      excerpts.exit().remove()
      excerpts.select('blockquote').text (d) =>
        d.message.annotation.quote.replace(/\u00a0/g, ' ')  # replace &nbsp;

      highlights = []
      excerpts.each (d) =>
        h = d.message.annotation.hash
        if h then highlights.push h.valueOf()
      @provider.setActiveHighlights highlights

      while items.length
        items.enter().append('li').classed('hyp-annotation', true)
        items.exit().remove()
        items
          .each (d) ->
            _t = this and d3.select(this)
            unless _t and _t.classed('hyp-detail')
              _t.html Handlebars.templates.detail d.message.annotation
          .classed('hyp-paper', (c) -> not c.parent.message?)
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

          .on 'mouseup', =>
            event = d3.event
            target = event.target
            unless target.tagName is 'A' then return
            event.stopPropagation()

            animate = (parent) ->
              collapsed = parent.classed('hyp-collapsed')
              parent.select('.hyp-thread')
                .transition().duration(200)
                  .style('overflow', 'hidden')
                  .style 'height', ->
                    if collapsed
                      "0px"
                    else
                      "#{$(this).children().outerHeight(true)}px"
                  .each 'end', ->
                    unless collapsed
                      d3.select(this)
                        .style('height', null)
                        .style('overflow', null)

            parent = d3.select(event.currentTarget)
            switch d3.event.target.getAttribute('href')
              when '#collapse'
                d3.event.preventDefault()
                collapsed = parent.classed('hyp-collapsed')
                animate parent.classed('hyp-collapsed', !collapsed)
              when '#reply'
                unless @plugins.Permissions?.user
                  showAuth true
                  break
                d3.event.preventDefault()
                parent = d3.select(event.currentTarget)
                animate parent.classed('hyp-collapsed', false)
                reply = this.createAnnotation()
                reply.thread = this.threadId(parent.datum().message.annotation)

                editor = this._createEditor()
                editor.load(reply)
                editor.element.removeClass('annotator-outer')
                editor.on 'save', (annotation) =>
                  this.publish 'annotationCreated', [annotation]

                d3.select(editor.element[0]).select('form')
                  .data([reply])
                    .html(Handlebars.templates.editor)
                    .on 'mouseover', => d3.event.stopPropagation()

                item = d3.select(d3.event.currentTarget)
                  .select('.annotator-listing')
                  .insert('li', '.hyp-annotation')
                    .classed('hyp-annotation', true)
                    .classed('hyp-writer', true)

                editor.element.appendTo(item.node())
                editor.on('hide', => item.remove())
                editor.element.find(":input:first").focus()

        context = items.select '.hyp-thread'
        items = thread context, '.hyp-annotation'

    @editor.hide()
    @viewer.show()

  updateViewer: (annotations) =>
    existing = d3.select(@viewer.element[0]).datum()
    if existing?
      annotations = existing.flattenChildren()?.map((c) -> c.annotation)
        .concat(annotations)
    this.showViewer(annotations or [], @detail)

  showEditor: (annotation) =>
    if not annotation.user?
      @plugins.Permissions.addFieldsToAnnotation(annotation)

    @viewer.hide()
    @editor.load(annotation)
    @editor.element.find('.annotator-controls').remove()

    quote = annotation.quote.replace(/\u00a0/g, ' ') # replace &nbsp;
    excerpt = $('<li class="hyp-paper hyp-excerpt">')
    excerpt.append($("<blockquote>#{quote}</blockquote>"))

    item = $('<li class="hyp-paper hyp-writer">')
    item.append($(Handlebars.templates.editor(annotation)))

    @editor.element.find('.annotator-listing').empty()
      .append(excerpt)
      .append(item)
      .find(":input:first").focus()

    d3.select(@viewer.element[0]).datum(null)
    this.show()

  show: =>
    if @detail
      annotations = d3.select(@viewer.element[0]).datum().children.map (c) =>
        c.message.annotation.hash.valueOf()
    else
      annotations = @heatmap.buckets[@bucket]?.map (a) => a.hash.valueOf()

    @visible = true
    @provider.setActiveHighlights annotations
    @provider.showFrame()
    $("#toolbar").addClass "shown"

  hide: =>
    @visible = false
    @provider.setActiveHighlights []
    @provider.hideFrame()
    $("#toolbar").removeClass "shown"


  threadId: (annotation) ->
    if annotation?.thread?
      annotation.thread + '/' + annotation.id
    else
      annotation.id

window.Hypothesis = Hypothesis
