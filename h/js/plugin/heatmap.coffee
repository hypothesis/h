class Annotator.Plugin.Heatmap extends Annotator.Plugin

  # prototype constants
  this::BUCKET_THRESHOLD_PAD = 40
  this::BUCKET_SIZE = 50

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

  _collate: (a, b) =>
    for i in [0..a.length-1]
      if a[i] < b[i]
        return -1
      if a[i] > b[i]
        return 1
    return 0

  _colorize: (v) ->
    c = d3.scale.pow().exponent(2)
      .range([0, 10])
    l = d3.scale.pow().exponent(.5)
      .domain([0, 1])
      .range([100, 50])
    d3.hcl(270, c(v), l(v)).toString()

  updateHeatmap: (data) =>
    return unless d3?

    wrapper = this.element.offsetParent()
    {highlights, offset} = data

    # Keep track of buckets of annotations above and below the viewport
    above = []
    below = []

    # Construct control points for the heatmap highlights
    points = $.map highlights, (hl, i) =>
      x = hl.offset.top - wrapper.offset().top - offset
      h = hl.height
      d = hl.data

      if x <= @BUCKET_SIZE + @BUCKET_THRESHOLD_PAD
        if d not in above then above.push d
      else if x + h >= $(window).height() - @BUCKET_SIZE
        if d not in below then below.push d
      else
        return [
          [x, 1, d]
          [x + h, -1, d]
        ]
      return []

    # Accumulate the overlapping annotations into buckets
    {@buckets, @index, max} = points.sort(this._collate)
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
      # TODO: dynamic programming
      small = 0
      threshold = min = 60
      for i in [0..@index.length-2]
        # ignore buckets followed by an empty bucket
        # prevents erroneous deletion of isolated buckets
        if @buckets[i+1].length and (w = @index[i+1] - @index[i]) < min
          small = i
          min = w
          break if min == 0 # short-circuit optimization

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
      x2 = if @index[i+1]? then @index[i+1] else wrapper.height()
      offsets = [@index[i], x2]
      if annotations.length
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
        curve(v).slice() for v in d3.range(0, 1, .05)
      else
        [ [offsets[0], i, 0, 1e-6]
          [offsets[1], i, 1, 1e-6] ]
    )

    # And a little opacity spice
    opacity = d3.scale.pow().domain([0, max]).range([.1, .6]).exponent(2)

    # d3 selections
    stops = d3.select(@element[0]).datum(data) # cache highlights
      .select('#heatmap-gradient')
      .selectAll('stop').data(stopData, (d) => d)
    stops.enter().append('stop')
    stops.exit().remove()
    stops.order()
      .attr('offset', (v) => v[0] / $(window).height())
      .attr('stop-color', (v) =>
        if max == 0 then this._colorize(1e-6) else this._colorize(v[3] / max))
      .attr('stop-opacity', (v) ->
        if max == 0 then .1 else opacity(v[3]))

    @buckets.unshift above, []
    @buckets.push below, []
    @index.unshift @BUCKET_THRESHOLD_PAD,
      (@BUCKET_THRESHOLD_PAD + @BUCKET_SIZE)
    @index.push $(window).height() - @BUCKET_SIZE, $(window).height()

    this.publish('updated')

  isUpper: (i) => i == 0
  isLower: (i) => i == @index.length - 2
