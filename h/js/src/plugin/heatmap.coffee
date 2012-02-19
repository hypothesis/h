class Annotator.Plugin.Heatmap extends Annotator.Plugin
  classes:
    hl:
      hide:   'annotator-hl-filtered'
      active: 'annotator-hl-active'

  # HTML templates for the plugin UI.
  html:
    element: """
             <svg class="annotator-heatmap"
                  xmlns="http://www.w3.org/2000/svg"
                  xmlns:xlink="http://www.w3.org/1999/xlink">
                <defs>
                  <linearGradient id="bgGradient"
                                  x1="0%" y1="0%"
                                  x2="100%" y2="0%">
                    <stop offset="20%" stop-color="#ffffff" stop-opacity="1" />
                    <stop offset="40%" stop-color="#f2f0e3" stop-opacity="0" />
                    <stop offset="100%" stop-color="#000000" stop-opacity="1" />
                  </linearGradient>
                  <linearGradient id="heatmapGradient"
                                  x1="0%" y1="0%"
                                  x2="0%" y2="100%">
                  </linearGradient>
                  <filter id="heatBlend">
                    <feGaussianBlur stdDeviation="1"><feGaussianBlur>
                    <feBlend mode="screen" in="SourceAlpha"><feBlend>
                  </filter>
                </defs>
                <rect x="0" y="0" width="100%" height="100%"
                      fill="url(#heatmapGradient)"
                      filter="url(#heatBlend)" />
                <rect x="0" y="0" width="100%" height="100%"
                      fill="url(#bgGradient)" />
             </svg>
             """ #" coffee-mode font lock bug

    options:
      message: Annotator._t("Sorry, some features of the Annotator failed to load.")

  # Initializes the heatmap plugin
  pluginInit: ->
    @heatmap = $(@html.element)
    @heatmap.appendTo(@annotator.wrapper)

    this._setupListeners()

    unless d3? or @d3?
        console.error('d3.js is required to use the heatmap plugin')
    if not d3?
      $.getScript(@d3, @updateHeatmap)
        .error(->
          Annotator.showNotification(@options.message))

  # Public: Creates a new instance of the Heatmap plugin.
  #
  # element - The Annotator element (this is ignored by the plugin).
  # options - An Object literal of options.
  #
  # Returns a new instance of the plugin.
  constructor: (element, options) ->
    super element, options
    @d3 = options.d3

  # Listens to annotation change events on the Annotator in order to refresh
  # the @annotations collection.
  # TODO: Make this more granular so the entire collection isn't reloaded for
  # every single change.
  #
  # Returns itself.
  _setupListeners: ->
    events = [
      'annotationsLoaded', 'annotationCreated',
      'annotationUpdated', 'annotationDeleted'
    ]

    for event in events
      @annotator.subscribe event, this.updateHeatmap
    this

    $(window).scroll this.updateHeatmap
    $(window).resize this.updateHeatmap

  # Public: Updates the @heatmap property with the latest annotation
  # elements in the DOM.
  #
  # Returns a jQuery collection of the elements.
  updateHeatmap: =>
    context = @annotator.wrapper.context
    scale = context.scrollHeight / window.innerHeight
    translate = window.pageYOffset / context.scrollHeight * scale

    # Get the heatmap gradient
    gradient = d3.select(@heatmap.find('#heatmapGradient').get(0))
    # Translate it based on the window scroll
    gradient.attr('gradientTransform', "translate(0,-#{translate})")

    # Get all the visible annotations
    annotations = @annotator.element.find('.annotator-hl:visible')

    # Calculate gradient stops from the annotations ...
    {points, _, max} = annotations
      # ... get the top and height of each annotation
      .map () ->
        {
          top: $(this).offset().top / context.scrollHeight * scale
          height: $(this).innerHeight() / context.scrollHeight * scale
        }
       # ... de-jQuery-ify to get the underlying array
      .get()
      # ... calculate the gradient control points
      .reduce((acc, m) ->
        acc.concat [
          [m.top, 0]
          [m.top + 0.5 * m.height, 1]
          [m.top + m.height, -1]
        ]
      , [[0,0], [scale,0]])
      # ... then sort the points and count the overlap
      .sort()
      .reduce((acc, n) ->
        [y, d] = n
        acc.count += d
        acc.points.push {
          offset: y,
          count: acc.count
        }
        acc.max = acc.count if acc.count > acc.max
        acc
      , {
        points: []
        count: 0
        max: 0
      })

    # Bind the heatmap to the control points
    heatmap = gradient.selectAll('stop').data(points)

    # Colorize it
    heatmap.enter().append("stop")

    heatmap
      .attr("offset", (p) -> p.offset)
      .attr("stop-color", (p) ->
        v = (p.count / max)

        # calculate the color components, blue to red
        r = if 0.6 <= v then 100 * Math.abs(v - 0.6) * 2.5 else 0
        g = 100 * (1 - Math.abs(2*v - 1))
        b = if v < 0.4 then 100 * (0.4 - v) / 0.4 else 0
        "rgb(#{r}%, #{g}%, #{b}%)"
      )
      .attr("stop-opacity", (p) -> d3.scale.pow().domain([0,max])(p.count))

    heatmap.exit().remove()
