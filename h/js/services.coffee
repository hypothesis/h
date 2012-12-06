class Hypothesis extends Annotator
  # Plugin configuration
  options:
    Heatmap: {}
    Permissions:
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')

  # Internal state
  bucket: -1         # * The index of the bucket shown in the summary view
  detail: false      # * Whether the viewer shows a summary or detail listing
  hash: -1           # * cheap UUID :cake:
  cache: {}          # * object cache
  visible: false     # * Whether the sidebar is visible
  unsaved_drafts: [] # * Unsaved drafts currenty open

  this.$inject = ['$document']
  constructor: ($document) ->
    super

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    # Establish cross-domain communication to the widget host
    @provider = new easyXDM.Rpc
      swf: @options.swf
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
          if @plugins.Permissions.user?
            @cache[h = ++@hash] = this.createAnnotation()
            h
          else
            this.showAuth true
            this.show()
            null
        showEditor: (stub) =>
          return unless this._canCloseUnsaved()
          h = stub.hash
          annotation = $.extend @cache[h], stub,
            hash:
              toJSON: => undefined
              valueOf: => h
          this.showEditor annotation
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
        dragFrame: {}
        getHighlights: {}
        setActiveHighlights: {}
        getMaxBottom: {}
        scrollTop: {}

  _initialize: =>
    # Set up interface elements
    this._setupHeatmap()
    @heatmap.element.appendTo(document.body)

    @provider.getMaxBottom (max) =>
      @element.find('#toolbar').css("top", "#{max}px")
      @element.find('#gutter').css("margin-top", "#{max}px")
      @heatmap.BUCKET_THRESHOLD_PAD = (
        max + @heatmap.constructor.prototype.BUCKET_THRESHOLD_PAD
      )

    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      annotation.created = annotation.updated = (new Date()).toString()
      annotation.user = @plugins.Permissions.options.userId(
        @plugins.Permissions.user)

    this.publish 'hostUpdated'

  _setupWrapper: ->
    @wrapper = @element.find('#wrapper')
    .on 'mousewheel', (event, delta) ->
      # prevent overscroll from scrolling host frame
      # This is actually a bit tricky. Starting from the event target and
      # working up the DOM tree, find an element which is scrollable
      # and has a scrollHeight larger than its clientHeight.
      # I've obsered that some styles, such as :before content, may increase
      # scrollHeight of non-scrollable elements, and that there a mysterious
      # discrepancy of 1px sometimes occurs that invalidates the equation
      # typically cited for determining when scrolling has reached bottom:
      #   (scrollHeight - scrollTop == clientHeight)
      $current = $(event.target)
      while (
        ($current.css('overflow') in ['visible', '']) or
        ($current[0].scrollHeight == $current[0].clientHeight)
      )
        $current = $current.parent()
        if not $current[0]? then return event.preventDefault()
      scrollTop = $current[0].scrollTop
      scrollEnd = $current[0].scrollHeight - $current[0].clientHeight
      if delta > 0 and scrollTop == 0
        event.preventDefault()
      else if delta < 0 and scrollEnd - scrollTop <= 1
        event.preventDefault()
    this

  _setupDocumentEvents: ->
    @element.find('#toolbar .tri').click =>
      if @visible
        this.hide()
      else
        if @viewer.isShown() and @bucket == -1
          this._fillDynamicBucket()
        this.show()

    el = document.createElementNS 'http://www.w3.org/1999/xhtml', 'canvas'
    el.width = el.height = 1
    @element.append el

    handle = @element.find('#toolbar .tri')[0]
    handle.addEventListener 'dragstart', (event) =>
      event.dataTransfer.setData 'text/plain', ''
      event.dataTransfer.setDragImage(el, 0, 0)
      @provider.dragFrame event.screenX
    handle.addEventListener 'dragend', (event) =>
      @provider.dragFrame event.screenX
    @element[0].addEventListener 'dragover', (event) =>
      @provider.dragFrame event.screenX
    @element[0].addEventListener 'dragleave', (event) =>
      @provider.dragFrame event.screenX

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
        .selectAll('div.heatmap-pointer')
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
        .classed('heatmap-pointer', true)

      tabs.exit().remove()

      tabs

        .style 'top', (d) =>
          "#{(@heatmap.index[d] + @heatmap.index[d+1]) / 2}px"

        .html (d) =>
          "<div class='label'>#{@heatmap.buckets[d].length}</div><div class='svg'></div>"

        .classed('upper', @heatmap.isUpper)
        .classed('lower', @heatmap.isLower)

        .style 'display', (d) =>
          if (@heatmap.buckets[d].length is 0) then 'none' else ''

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

    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = this._createEditor()
    .on 'hide save', =>
      if @unsaved_drafts.indexOf(@editor) > -1
        @unsaved_drafts.splice(@unsaved_drafts.indexOf(@editor), 1)
    .on 'hide', =>
      @provider.onEditorHide()
    .on 'save', =>
      @provider.onEditorSubmit()
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

    @unsaved_drafts.push editor
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
    if (@visible and not detail) or @unsaved_drafts.indexOf(@editor) > -1
      if not this._canCloseUnsaved() then return

    # Not implemented

  showEditor: (annotation) =>
    if not annotation.user?
      @plugins.Permissions.addFieldsToAnnotation(annotation)

    @viewer.hide()
    @editor.load(annotation)
    @editor.element.find('.annotator-controls').remove()

    quote = annotation.quote.replace(/\u00a0/g, ' ') # replace &nbsp;
    excerpt = $('<li class="paper excerpt">')
    excerpt.append($("<blockquote>#{quote}</blockquote>"))

    item = $('<li class="annotation paper writer">')
    item.append($(Handlebars.templates.editor(annotation)))

    @editor.element.find('.annotator-listing').empty()
      .append(excerpt)
      .append(item)
      .find(":input:first").focus()

    @unsaved_drafts.push @editor

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
    @element.find('#toolbar').addClass('shown')
      .find('.tri').attr('draggable', true)

  hide: =>
    @lastWidth = window.innerWidth
    @visible = false
    @provider.setActiveHighlights []
    @provider.hideFrame()
    @element.find('#toolbar').removeClass('shown')
      .find('.tri').attr('draggable', false)

  _canCloseUnsaved: ->
    # See if there's an unsaved/uncancelled reply
    can_close = true
    open_editors = 0
    for editor in @unsaved_drafts
      unsaved_text = editor.element.find(':input:first').attr 'value'
      if unsaved_text? and unsaved_text.toString().length > 0
        open_editors += 1

    if open_editors > 0
      if open_editors > 1
        ctext = "You have #{open_editors} unsaved replies."
      else
        ctext = "You have an unsaved reply."
      ctext = ctext + " Do you really want to close the view?"
      can_close = confirm ctext

    if can_close then @unsaved_drafts = []
    can_close

  threadId: (annotation) ->
    if annotation?.thread?
      annotation.thread + '/' + annotation.id
    else
      annotation.id


angular.module('h.services', [])
  .service('annotator', Hypothesis)
