$ = Annotator.$

util =
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
        className: 'annotator-frame annotator-collapsed'
        style:
          visibility: 'hidden'
      remote: @app
    ,
      local:
        publish: (args..., k, fk) => this.publish args...
        setupAnnotation: => this.setupAnnotation arguments...
        onEditorHide: this.onEditorHide
        onEditorSubmit: this.onEditorSubmit
        showFrame: => @frame.removeClass('annotator-collapsed')
        hideFrame: => @frame.addClass('annotator-collapsed')
        getHighlights: =>
          highlights: $(@wrapper).find('.annotator-hl').map ->
            offset: $(this).offset()
            height: $(this).outerHeight(true)
            data: $(this).data('annotation').hash
          .get()
          offset: $(@wrapper[0].ownerDocument).scrollTop()
        setActiveHighlights: (hashes=[]) =>
          @wrapper.find('.annotator-hl')
          .each ->
            if $(this).data('annotation').hash in hashes
              $(this).addClass('annotator-hl-active')
            else
              $(this).removeClass('annotator-hl-active')
        getMaxBottom: =>
          sel = '*' + (":not(.annotator-#{x})" for x in [
            'adder', 'outer', 'notice', 'filter', 'frame'
          ]).join('')

          # use the maximum bottom position in the page
          all = for el in $(document.body).find(sel)
            p = $(el).css('position')
            t = $(el).offset().top
            z = $(el).css('z-index')
            if (p == 'absolute' or p == 'fixed') and t == 0 and z != 'auto'
              bottom = $(el).offset().top + $(el).outerHeight(false)
              # but don't go larger than 80, because this isn't bulletproof
              if bottom > 80 then 0 else bottom
            else
              0
          Math.max.apply(Math, all)
        scrollTop: (y) => $(window).scrollTop y
      remote:
        publish: {}
        addPlugin: {}
        createAnnotation: {}
        showEditor: {}
        update: {}

    $(window).on 'resize scroll', util.debounce => @consumer.update()

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