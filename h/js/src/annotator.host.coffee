class Annotator.Host extends Annotator
  # Events to be bound on Annotator#element.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  # Plugin configuration
  options: {}

  # timer used to throttle event frequency
  updateTimer: null

  constructor: (element, options) ->
    super

    @app = @options.app
    delete @options.app

    # Load plugins
    for own name, opts of @options
      if not @plugins[name]
        this.addPlugin(name, opts)

    # Establish cross-domain communication
    @consumer = new easyXDM.Rpc
      channel: 'annotator'
      container: @wrapper[0]
      local: options.local
      onReady: () ->
        frame = $(this.container).find('[src^="'+@props.src+'"]')
          .css('visibility', 'visible')
        window.annotator.frame = frame
      swf: options.swf
      props:
        className: 'hyp-iframe hyp-collapsed'
        style:
          visibility: 'hidden'
      remote: @app
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        getHighlights: =>
          highlights: $(@wrapper).find('.annotator-hl').map ->
            position: $(this).position()
            height: $(this).outerHeight(true)
            data: $(this).data('annotation').hash
          .get()
          offset: $(@wrapper[0].ownerDocument).scrollTop()
        setupAnnotation: => this.setupAnnotation arguments...
        onEditorHide: this.onEditorHide
        onEditorSubmit: this.onEditorSubmit
        showFrame: =>
          @frame.removeClass('hyp-collapsed')
        hideFrame: =>
          @frame.addClass('hyp-collapsed')
      remote:
        publish: {}
        addPlugin: {}
        createAnnotation: {}
        showEditor: {}
        back: {}
        update: {}

    # Throttle resize events and update the heatmap
    throttledUpdate = () =>
      clearTimeout(@updateTimer) if @updateTimer?
      @updateTimer = setTimeout =>
        @updateTimer = null
        @consumer.update()

    $(window).resize(throttledUpdate).scroll(throttledUpdate)
    $(@wrapper).on 'mouseup', (event) =>
      @consumer.back() unless @ignoreMouseup

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: ->
    this

  _setupEditor: ->
    true

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    $(document).bind({
      "mouseup": this.checkForEndSelection
    })
    this

  showEditor: (annotation) =>
    stub =
      ranges: annotation.ranges
      quote: annotation.quote
      hash: annotation.hash
    if not stub.hash
      @consumer.createAnnotation (hash) =>
        annotation.hash = stub.hash = hash
        @consumer.showEditor stub
    else
      @consumer.showEditor stub

  publish: (event, args) ->
    if event in ['annotationCreated']
      [annotation] = args
      @consumer.publish event, [annotation.hash]
    super arguments...
