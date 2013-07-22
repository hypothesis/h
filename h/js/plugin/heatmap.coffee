class Annotator.Plugin.Heatmap extends Annotator.Plugin
  # prototype constants
  BUCKET_THRESHOLD_PAD: 40
  BUCKET_SIZE: 50


  # heatmap svg skeleton
  html: """
        <div class="annotator-heatmap">
          <svg xmlns="http://www.w3.org/2000/svg"
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
        </div>
        """

  # buckets of annotations that overlap
  buckets: []

  # index for fast hit detection in the buckets
  index: []

  constructor: (element, options) ->
    super $(@html), options
    this._rebaseUrls()
    @element.appendTo element

  _rebaseUrls: ->
    # We can't rely on browsers to implement the xml:base property correctly.
    # Therefore, we must rebase the fragment references we use in the SVG for
    # the heatmap in case the page contains a <base> tag which might otherwise
    # break these references.

    location = window.location
    base = "#{location.protocol}//#{location.host}#{location.pathname}"

    rect = @element.find('rect')
    fill = rect.attr('fill')
    filter = rect.attr('filter')

    fill = fill.replace(/(#\w+)/, "#{base}$1")
    filter = filter.replace(/(#\w+)/, "#{base}$1")

    rect.attr('fill', fill)
    rect.attr('filter', filter)

  _collate: (a, b) =>
    for i in [0..a.length-1]
      if a[i] < b[i]
        return -1
      if a[i] > b[i]
        return 1
    return 0

  _colorize: (v) ->
    c = d3.scale.pow().exponent(2)
    .domain([0, 1])
    .range(['#f7fbff', '#08306b'])
    .interpolate(d3.interpolateHcl)
    c(v).toString()

  updateHeatmap: (data) =>
    return unless d3?
    
    wrapper = this.element.offsetParent()
    {highlights, offset} = data

    # Keep track of buckets of annotations above and below the viewport
    above = []
    below = []

    # Construct control points for the heatmap highlights
    points = highlights.reduce (points, hl, i) =>
      x = hl.offset.top - wrapper.offset().top - offset
      h = hl.height
      d = hl.data

      if x <= @BUCKET_SIZE + @BUCKET_THRESHOLD_PAD
        if d not in above then above.push d
      else if x + h >= $(window).height() - @BUCKET_SIZE
        if d not in below then below.push d
      else
        points.push [x, 1, d]
        points.push [x + h, -1, d]
      points
    , []

    # Accumulate the overlapping annotations into buckets.
    # The algorithm goes like this:
    # - Collate the points by sorting on position then delta (+1 or -1)
    # - Reduce over the sorted points
    #   - For +1 points, add the annotation at this point to an array of
    #     "carried" annotations. If it already exists, increase the
    #     corresponding value in an array of counts which maintains the
    #     number of points that include this annotation.
    #   - For -1 points, decrement the value for the annotation at this point
    #     in the carried array of counts. If the count is now zero, remove the
    #     annotation from the carried array of annotations.
    #   - If this point is the first, last, sufficiently far from the previous,
    #     or there are no more carried annotations, add a bucket marker at this
    #     point.
    #   - Otherwise, if the last bucket was not isolated (the one before it
    #     has at least one annotation) then remove it and ensure that its
    #     annotations and the carried annotations are merged into the previous
    #     bucket.
    {@buckets, @index} = points
    .sort(this._collate)
    .reduce ({buckets, index, carry}, [x, d, a], i, points) =>
      if d > 0                                            # Add annotation
        if (j = carry.annotations.indexOf a) < 0
          carry.annotations.unshift a
          carry.counts.unshift 1
        else
          carry.counts[j]++
      else                                                # Remove annotation
        j = carry.annotations.indexOf a                   # XXX: assert(i >= 0)
        if --carry.counts[j] is 0
          carry.annotations.splice j, 1
          carry.counts.splice j, 1

      if (
        (index.length is 0 or i is points.length - 1) or  # First or last?
        carry.annotations.length is 0 or                  # A zero marker?
        x - index[index.length-1] > 180                   # A large gap?
      )                                                   # Mark a new bucket.
        buckets.push carry.annotations.slice()
        index.push x
      else
        # Merge the previous bucket, making sure its predecessor contains
        # all the carried annotations and the annotations in the previous
        # bucket.
        if buckets[buckets.length-2]?.length
          last = buckets[buckets.length-2]
          toMerge = buckets.pop()
          index.pop()
        else
          last = buckets[buckets.length-1]
          toMerge = []
        last.push a0 for a0 in carry.annotations when a0 not in last
        last.push a0 for a0 in toMerge when a0 not in last

      {buckets, index, carry}
    ,
      buckets: []
      index: []
      carry:
        annotations: []
        counts: []
        latest: 0

    # Add the scroll buckets
    @buckets.unshift [], above, []
    @buckets.push below, []
    @index.unshift 0, @BUCKET_THRESHOLD_PAD,
      (@BUCKET_THRESHOLD_PAD + @BUCKET_SIZE)
    @index.push $(window).height() - @BUCKET_SIZE, $(window).height()

    # Calculate the total count for each bucket (including replies) and the
    # maximum count.
    max = 0
    for b in @buckets
      total = b.reduce (total, a) ->
        subtotal = (a.thread?.flattenChildren()?.length or 0) + 1
        total + subtotal
      , 0
      max = Math.max max, total
      b.total = total

    # Set up the stop interpolations for data binding
    stopData = $.map @buckets, (bucket, i) =>
      x2 = if @index[i+1]? then @index[i+1] else wrapper.height()
      offsets = [@index[i], x2]
      if bucket.total
        start = @buckets[i-1]?.total and ((@buckets[i-1].total + bucket.total) / 2) or 1e-6
        end = @buckets[i+1]?.total and ((@buckets[i+1].total + bucket.total) / 2) or 1e-6
        curve = d3.scale.pow().exponent(.1)
          .domain([0, .5, 1])
          .range([
            [offsets[0], i, 0, start]
            [d3.mean(offsets), i, .5, bucket.total]
            [offsets[1], i, 1, end]
          ])
          .interpolate(d3.interpolateArray)
        curve(v) for v in d3.range(0, 1, .05)
      else
        [ [offsets[0], i, 0, 1e-6]
          [offsets[1], i, 1, 1e-6] ]

    # Update the data bindings
    element = d3.select(@element[0]).datum(data)

    # Update gradient stops
    opacity = d3.scale.pow().domain([0, max]).range([.1, .6]).exponent(2)

    stops = element
    .select('#heatmap-gradient')
    .selectAll('stop')
    .data(stopData, (d) => d)

    stops.enter().append('stop')
    stops.exit().remove()
    stops.order()
      .attr('offset', (v) => v[0] / $(window).height())
      .attr('stop-color', (v) =>
        if max == 0 then this._colorize(1e-6) else this._colorize(v[3] / max))
      .attr('stop-opacity', (v) ->
        if max == 0 then .1 else opacity(v[3]))

    # Update bucket pointers
    tabs = element
    .selectAll('div.heatmap-pointer')

    .data =>
      buckets = []
      @index.forEach (b, i) =>
        if @buckets[i].length > 0 or @isUpper(i) or @isLower(i)
          buckets.push i
      buckets

    tabs.enter().append('div')
      .classed('heatmap-pointer', true)

    tabs.exit().remove()

    tabs
    .style 'top', (d) =>
      "#{(@index[d] + @index[d+1]) / 2}px"

    .html (d) =>
      "<div class='label'>#{@buckets[d].total}</div><div class='svg'></div>"

    .classed('upper', @isUpper)
    .classed('lower', @isLower)

    .style 'display', (d) =>
      if (@buckets[d].length is 0) then 'none' else ''

    this.publish('updated')

  isUpper: (i) => i == 1
  isLower: (i) => i == @index.length - 2
