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

    # TODO: highlights?
    #this.subscribe 'beforeAnnotationCreated', (annotation) =>
    #  this.setupAnnotation(annotation, false)

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
        addPlugin: => this.addPlugin arguments...
        setupAnnotation: => this.setupAnnotation arguments...
        getHighlights: =>
          result = $(wrapper).find('.annotator-hl').map ->
            position = $(this).position()
            position.height = $(this).outerHeight(true)
            position.data = $(this).data('annotation')
            position
          highlights: result.get()
          offset: $(wrapper.ownerDocument).scrollTop()
        loadAnnotations: => this.loadAnnotations arguments...
        showFrame: =>
          @frame.removeClass('hyp-collapsed')
        hideFrame: =>
          @frame.addClass('hyp-collapsed')
      remote:
        publish: {}
        subscribe: {}
        addPlugin: {}
        showViewer: {}
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
    $(wrapper).on 'click', (event) =>
      @consumer.back()

  # Creates an instance of Annotator.Viewer and assigns it to the @viewer
  # property, appends it to the @wrapper and sets up event listeners.
  #
  # Returns itself to allow chaining.
  _setupViewer: ->
    @viewer =
      element: $('<span></span>')
    this

  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: (annotation) ->
    @editor =
      element: $('<span></span>')
      load: (annotation) =>
        @consumer.showEditor annotation
      show: =>
        console.log('yar?')
        #@host.publish('editor', ['show', annotation])

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    $(document).bind({
      "mouseup": this.checkForEndSelection
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
  setupAnnotation: (annotation, fireEvents=true) ->
    annotation = super(annotation, false)
    annotation.highlights.toJSON = => undefined # Don't serialize highlights
    if fireEvents
      this.publish('annotationCreated', [annotation])

  # Annotator#element callback. Displays the @editor in place of the @adder and
  # loads in a newly created annotation Object. The click event is used as well
  # as the mousedown so that we get the :active state on the @adder when clicked
  #
  # event - A mousedown Event object
  #
  # Returns nothing.
  onAdddderClick: (event) =>
    event?.preventDefault()

    position = @adder.position()
    @adder.hide()

    # Create an annotation and display the editor.
    this.showEditor(this.createAnnotation(), position)

  publish: ->
    # Echo published events to the iframe
    @consumer.publish arguments...
    super arguments...
