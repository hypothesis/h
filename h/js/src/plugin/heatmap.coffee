class Annotator.Plugin.Heatmap extends Annotator.Plugin
  # heatmap svg skeleton
  html: """
        <svg class="annotator-heatmap"
             xmlns="http://www.w3.org/2000/svg"
             version="1.1">
           <defs>
             <linearGradient id="heatmap-gradient" x2="0" y2="100%">
             </linearGradient>
             <filter id="heatmap-blur">
               <feGaussianBlur stdDeviation="0 2"></feGaussianBlur>
             </filter>
           </defs>
           <rect x="0" y="0" width="100%" height="100%"
                 fill="url('#heatmap-gradient')"
                 filter="url('#heatmap-blur')" >
           </rect>
         </svg>
         """

  options:
    message: Annotator._t("Sorry, some features of the Annotator failed to load.")

  # timer used to throttle heatmap recalculation frequency
  updateTimer: null

  # buckets of annotations that overlap
  buckets: []

  # index for fast hit detection in the buckets
  index: []

  constructor: (element, options) ->
    super $(@html, options)

  pluginInit: ->
    if d3?
      this._setupListeners()
      this.updateHeatmap()
    else if @options.d3?
      setTimeout(
        =>
          $.getScript(@options.d3, =>
            this._setupListeners()
            this.updateHeatmap()
          ).error(-> Annotator.showNotification(@options.message))
      , 0)
    else
      Annotator.showNotification(@options.message)

  # Listens to annotation change events on the Annotator in order to refresh
  # the @annotations collection.
  # TODO: Make this more granular so the entire collection isn't reloaded for
  # every single change.
  #
  # Returns itself.
  _setupListeners: ->
    events = [
      'annotationsLoaded'
      'annotationCreated'
      'annotationUpdated'
      'annotationDeleted'
    ]

    for event in events
      @annotator.subscribe event, this.updateHeatmap

    # Throttle resize events and update the heatmap
    throttledUpdate = () =>
      clearTimeout(@updateTimer) if @updateTimer?
      @updateTimer = setTimeout(
        () =>
          @updateTimer = null
          this.updateHeatmap()
        10
      )

    $(window).resize(throttledUpdate).scroll(throttledUpdate)

  _colorize: (v) ->
    s = d3.scale.pow().exponent(8)
      .range([0, .3])
    l = d3.scale.pow().exponent(.5)
      .domain([0, 1])
      .range([1, .45])
    d3.hsl(210, s(v), l(v)).toString()

  updateHeatmap: =>
    return unless d3?

    wrapper = $(@annotator.wrapper)
    highlights = @annotator.element.find('.annotator-hl:visible')
    offset = wrapper.offsetParent().scrollTop()

    # Re-set the 100% because some browsers might not adjust to events like
    # user zoom change properly.
    @element.css({height: '100%'})

    # Construct control points for the heatmap highlights
    points = highlights.map () ->
      x = $(this).offset().top - wrapper.offset().top - offset
      h = $(this).outerHeight(true)
      if x + h < 0 or x + h > $(window).outerHeight() then return []
      data = $(this).data('annotation')
      [ [x, 1, data],
        [x + h, -1, data] ]
    .get() # de-jQuery

    # Sort the points and reduce to accumulate the annotation list which follows
    # and the running overlap count at each stop.
    {@buckets, @index, max} = points.sort().reduce(
      ({annotations, buckets, index, max}, [x, d, a]) ->
        # use split and merge to eliminate any duplicates
        annotations = d3.merge(d3.split(annotations, (b) -> a is b))
        if d > 0
          annotations.push a
          max = Math.max(max, annotations.length)
        buckets.push annotations
        index.push x
        {annotations, buckets, index, max}
      ,
      annotations: []
      buckets: []
      index: []
      max: 0
    )

    # Set up the stop interpolations for data binding
    stopData = $.map(@buckets, (annotations, i) =>
      if annotations.length
        x2 = if @index[i+1]? then @index[i+1] else wrapper.height()
        offsets = [@index[i], x2]
        start = @buckets[i-1]?.length or 1e-6
        end = @buckets[i+1]?.length or 1e-6

        curve = d3.scale.pow().exponent(.1)
          .domain([0, .5, 1])
          .range([
            [offsets[0], i, 0, start]
            [d3.mean(offsets), i, .5, annotations.length]
            [offsets[1], i, 1, end]
          ])
          .interpolate(d3.interpolateArray)
        curve(v).slice() for v in d3.range(0, 1.1, .1)
    )

    # And a little opacity spice
    opacity = d3.scale.pow().domain([0, max]).exponent(.25)

    # d3 selections
    stops = d3.select(@element[0])
      .select('#heatmap-gradient')
      .selectAll('stop').data(stopData)
    stops.enter().append('stop')
    stops.exit().remove()
    stops.sort()
      .attr('offset', (v) => v[0] / $(window).outerHeight())
      .attr('stop-color', (v) => this._colorize(v[3] / max))
      .attr('stop-opacity', (v) -> opacity(v[3]))

    this.publish('updated')

  highlight: (bucket, fn) =>
    annotations = @buckets[bucket] or []
    lights = d3.select(@annotator.wrapper[0]).selectAll('.annotator-hl')
    lights.classed 'hyp-active', fn or ->
      $(this).data('annotation') in annotations
