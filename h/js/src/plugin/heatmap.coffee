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

  # buckets of annotations that overlap
  buckets: []

  # index for fast hit detection in the buckets
  index: []

  constructor: (element, options) ->
    super $(@html, options)

  _colorize: (v) ->
    s = d3.scale.pow().exponent(2)
      .range([0, .1])
    l = d3.scale.pow().exponent(.5)
      .domain([0, 1])
      .range([1, .5])
    d3.hsl(210, s(v), l(v)).toString()

  updateHeatmap: (data) =>
    return unless d3?

    wrapper = this.element.offsetParent()
    {highlights, offset} = data

    # Construct control points for the heatmap highlights
    points = $.map highlights, (hl, i) ->
      x = hl.offset.top - wrapper.offset().top - offset
      h = hl.height
      if x < 0 or x + h > $(window).height() then return []
      data = hl.data
      [ [x, 1, data],
        [x + h, -1, data] ]

    # Accumulate the overlapping annotations into buckets
    {@buckets, @index, max} = points

    # Sort the points by offset, with previous bucket tails before new heads
    .sort (a, b) =>
      for i in [0..a.length-1]
        if a[i] < b[i]
          return -1
        if a[i] > b[i]
          return 1
      return 0
    .reduce ({annotations, buckets, index, max}, [x, d, a], i, points) =>

        # remove all instances of this annotation from the accumulator
        annotations = d3.merge(d3.split(annotations, (b) => a is b))

        if d > 0
          # if this is a +1 control point, (re-)include the current annotation
          # by removing and then adding, duplicates are easily avoided
          annotations.push a
          buckets.push annotations
          index.push x
          max = Math.max(max, annotations.length)
        else
          # if this is a -1 control point, exclude the current annotation
          buckets.push annotations
          index.push x

        {annotations, buckets, index, max}
      ,
      annotations: []
      buckets: []
      index: []
      max: 0

    # Remove redundant points and merge close buckets until done
    while @buckets.length > 2

      # Find the two closest points
      small = 0
      threshold = min = 60
      for i in [0..@index.length-2]
        if (w = @index[i+1] - @index[i]) < min
          small = i
          min = w

      # Merge them if they are closer enough
      if min < threshold
        # Prefer merging the successor bucket backward but not if it's last
        # since the gradient must always return to 0 at the end
        if @buckets[small+2]?
          from = small + 1
          to = small

          for b in @buckets[from]
            @buckets[to].push b if b not in @buckets[to]
        else
          from = small

        # Drop the merged bucket and index
        @buckets.splice(from, 1)
        @index.splice(from, 1)
      else
        break

    # Set up the stop interpolations for data binding
    stopData = $.map(@buckets, (annotations, i) =>
      if annotations.length
        x2 = if @index[i+1]? then @index[i+1] else wrapper.height()
        offsets = [@index[i], x2]
        start = @buckets[i-1]?.length and ((@buckets[i-1].length + @buckets[i].length) / 2) or 1e-6
        end = @buckets[i+1]?.length and ((@buckets[i+1].length + @buckets[i].length) / 2) or 1e-6

        curve = d3.scale.pow().exponent(.1)
          .domain([0, .5, 1])
          .range([
            [offsets[0], i, 0, start]
            [d3.mean(offsets), i, .5, annotations.length]
            [offsets[1], i, 1, end]
          ])
          .interpolate(d3.interpolateArray)
        curve(v).slice() for v in d3.range(0, 1.05, .05)
    )

    # And a little opacity spice
    opacity = d3.scale.pow().domain([0, max]).range([.1, .6]).exponent(2)

    # d3 selections
    stops = d3.select(@element[0])
      .select('#heatmap-gradient')
      .selectAll('stop').data(stopData)
    stops.enter().append('stop')
    stops.exit().remove()
    stops.sort()
      .attr('offset', (v) => v[0] / $(window).height())
      .attr('stop-color', (v) => this._colorize(v[3] / max))
      .attr('stop-opacity', (v) -> opacity(v[3]))

    this.publish('updated')
