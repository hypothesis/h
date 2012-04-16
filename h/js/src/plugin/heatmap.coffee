class Annotator.Plugin.Heatmap extends Annotator.Plugin
  # HTML templates for the plugin UI.
  html:
    element: """
             <svg class="annotator-heatmap"
                  xmlns="http://www.w3.org/2000/svg"
                  xmlns:xlink="http://www.w3.org/1999/xlink">
                <defs>
                  <linearGradient id="heatmapGradient"
                                  x1="0%" y1="0%"
                                  x2="0%" y2="100%">
                  </linearGradient>
                  <filter id="heatBlend">
                    <feGaussianBlur stdDeviation="3"><feGaussianBlur>
                  </filter>
                </defs>
                <rect x="0" y="0" width="100%" height="100%"
                      fill="url(#heatmapGradient)"
                      filter="url(#heatBlend)" />
             </svg>
             """ #" coffee-mode font lock bug

    options:
      message: Annotator._t("Sorry, some features of the Annotator failed to load.")

  # Initializes the heatmap plugin
  pluginInit: ->
    @heatmap = $(@html.element)
    @heatmap.appendTo(@annotator.wrapper)

    unless d3? or @d3?
        console.error('d3.js is required to use the heatmap plugin')
    if not d3?
      setTimeout(
        =>
          $.getScript(@d3, =>
            this._setupListeners()
            this.updateHeatmap()
          ).error(-> Annotator.showNotification(@options.message))
      , 0)

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

    $(window).resize this.updateHeatmap

  _colorize: (v) ->
    # TODO: a better colorize function could incorporate confidence in
    # determining where to place the cutoffs for the first log step.
    v = v + 1 # prep for log scale
    h = d3.scale.log()
      .domain([1, 1.02, 1.5, 1.5, 2])
      .range([300, 300, 360, 0, 60])
    s = d3.scale.log()
      .domain([1, 1.01, 2])
      .range([0, 0.5, 1])
    l = d3.scale.log()
      .domain([1, 1.02, 1.1, 2])
      .range([0.75, 0.25, 0.375, 0.5])
    d3.hsl(h(v), s(v), l(v)).toString()

  # Public: Updates the @heatmap property with the latest annotation
  # elements in the DOM.
  #
  # Returns a jQuery collection of the elements.
  updateHeatmap: =>
    return unless d3?
    # Grab some attributes of the document for computing layout
    context = @annotator.wrapper.context
    scale = context.scrollHeight / window.innerHeight

    # Get all the visible annotations
    annotations = @annotator.element.find('.annotator-hl:visible')

    # Calculate gradient stops from the annotations ...
    {points, _, max} = annotations
      # ... get the top and height of each annotation
      .map () ->
        {
          el: this
          top: $(this).offset().top / context.scrollHeight
          height: $(this).innerHeight() / context.scrollHeight
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
      , [])
      # ... then sort the points and count the overlap
      .sort()
      .reduce((acc, n) ->
        [y, d] = n
        {points} = acc
        last = points[points.length-1]
        {offset, count} = last
        count += d
        if y is offset
          last.count = count
        else
          points.push
            offset: y,
            count: count
        acc.max = count if count > acc.max
        acc
      ,
        points: [offset: 0, count: 0]
        max: 1)

    # Bind the heatmap to the control points
    d3.select(@heatmap.get(0)).attr("height", context.scrollHeight)

    heatmap =
      d3.select(@heatmap.find('#heatmapGradient').get(0))
        .selectAll('stop').data(points, (p) -> p.offset)

    # Colorize it
    heatmap.enter().append("stop")
      .attr("stop-color", @_colorize 0)
      .transition().duration(1000)
        .attr("stop-color", (p) => @_colorize p.count / max)

    heatmap.order()
      .attr("offset", (p) -> p.offset)
      .transition().duration(250)
        .attr("stop-color", (p) => @_colorize p.count / max)

    heatmap.exit()
      .transition().duration(1000)
        .attr("stop-color", @_colorize 0)
        .remove()
