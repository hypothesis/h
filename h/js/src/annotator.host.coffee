utils =
  debounce: (delay=0, fn) =>
      timer = null
      =>
        if timer then clearTimeout(timer)
        setTimeout delay, =>
          timer = null
          fn()

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

    # Grab this for exporting the iframe from easyXDM
    annotator = this

    # Establish cross-domain communication
    @consumer = new easyXDM.Rpc
      channel: 'annotator'
      container: @wrapper[0]
      local: options.local
      onReady: () ->
        # `this` is otherwise hidden, private to the Rpc object's closures
        # so export the iframe element via the private `container` property
        frame = $(this.container).find('[src^="'+@props.src+'"]')
          .css('visibility', 'visible')
        annotator.frame = frame
      swf: options.swf
      props:
        className: 'hyp-iframe hyp-collapsed'
        style:
          visibility: 'hidden'
      remote: @app
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        setupAnnotation: => this.setupAnnotation arguments...
        onEditorHide: this.onEditorHide
        onEditorSubmit: this.onEditorSubmit
        showFrame: =>
          @frame.removeClass('hyp-collapsed')
        hideFrame: =>
          @frame.addClass('hyp-collapsed')
        getHighlights: =>
          highlights: $(@wrapper).find('.annotator-hl').map ->
            offset: $(this).offset()
            height: $(this).outerHeight(true)
            data: $(this).data('annotation').hash
          .get()
          offset: $(@wrapper[0].ownerDocument).scrollTop()
      remote:
        publish: {}
        addPlugin: {}
        createAnnotation: {}
        showEditor: {}
        back: {}
        update: {}

    $(window).on 'resize scroll', utils.debounce => @consumer.update()
    @wrapper.on 'mouseup', (event) =>
      @consumer.back() unless @ignoreMouseup

  publish: (event, args) ->
    if event in ['annotationCreated']
      [annotation] = args
      @consumer.publish event, [annotation.hash]
    super arguments...

  _setupWrapper: ->
    @wrapper = @element
    this

  # These methods aren't used in the iframe-hosted configuration of Annotator.
  _setupViewer: ->
    this

  _setupEditor: ->
    true

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

  setupAnnotation: (annotation) =>
    annotation = super

    # If any of the parents of the highlight elements are scrollable,
    # scrolling those should trigger an update.
    containers = $(annotation.highlights).parents()
    containers.off 'resize scroll', @consumer.update # don't register twice
    containers.on 'resize scroll', @consumer.update

    annotation