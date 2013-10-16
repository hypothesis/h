$ = Annotator.$

class Annotator.Plugin.Heatmap extends Annotator.Plugin
  # prototype constants
  BUCKET_THRESHOLD_PAD: 25
  BUCKET_SIZE: 50
  BOTTOM_CORRECTION: 14


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

  # Plugin configuration
  options:
    # gapSize parameter is used by the clustering algorithm
    # If an annotation is farther then this gapSize from the next bucket
    # then that annotation will not be merged into the bucket
    gapSize: 60

  # buckets of annotations that overlap
  buckets: []

  # index for fast hit detection in the buckets
  index: []

  # whether to update the viewer as the window is scrolled
  dynamicBucket: true

  constructor: (element, options) ->
    super $(@html), options

    if @options.container?
      $(@options.container).append @element
    else
      $(element).append @element

  pluginInit: ->
    return unless d3?
    this._maybeRebaseUrls()

    events = [
      'annotationCreated', 'annotationUpdated', 'annotationDeleted',
      'annotationsLoaded'
    ]
    for event in events
      if event is 'annotationCreated'
        @annotator.subscribe event, =>
          @dynamicBucket = false
          this._update()
      else
        @annotator.subscribe event, this._update

    @element.on 'click', (event) =>
      event.stopPropagation()
      this._fillDynamicBucket()
      @dynamicBucket = true

    $(window).on 'resize scroll', this._update
    $(document.body).on 'resize scroll', '*', this._update

    if window.PDFView?
      # XXX: PDF.js hack
      $(PDFView.container).on 'scroll', this._update

  _maybeRebaseUrls: ->
    # We can't rely on browsers to implement the xml:base property correctly.
    # Therefore, we must rebase the fragment references we use in the SVG for
    # the heatmap in case the page contains a <base> tag which might otherwise
    # break these references.

    return unless document.getElementsByTagName('base').length

    location = window.location
    base = "#{location.protocol}//#{location.host}#{location.pathname}"

    rect = @element.find('rect')
    fill = rect.attr('fill')
    filter = rect.attr('filter')

    fill = fill.replace(/(#\w+)/, "#{base}$1")
    filter = filter.replace(/(#\w+)/, "#{base}$1")

    rect.attr('fill', fill)
    rect.attr('filter', filter)

  _collate: (a, b) ->
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

  _update: =>
    wrapper = @annotator.wrapper
    highlights = wrapper.find('.annotator-hl')
    defaultView = wrapper[0].ownerDocument.defaultView

    # Keep track of buckets of annotations above and below the viewport
    above = []
    below = []
    comments = @annotator.comments.slice()

    # Construct control points for the heatmap highlights
    points = highlights.toArray().reduce (points, hl, i) =>
      d = $(hl).data('annotation')
      x = $(hl).offset().top - wrapper.offset().top - defaultView.pageYOffset
      h = $(hl).outerHeight(true)

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
        x - index[index.length-1] > @options.gapSize      # A large gap?
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
    @buckets.push below
    # Add comment bucket
    @buckets.push comments, []

    # Scroll up
    @index.unshift 0, @BUCKET_THRESHOLD_PAD,
      (@BUCKET_THRESHOLD_PAD + @BUCKET_SIZE)
    # Scroll down
    @index.push $(window).height() - @BUCKET_SIZE
    # If there are items in the comment bucket then it has be in the bottom
    # and possible lower bucket has to be slightly above it
    # if there are no comments, than the lower bucket has to travel lower to the page
    if comments.length
      @index.push $(window).height() - @BUCKET_SIZE + @BOTTOM_CORRECTION*2
      @index.push $(window).height() + @BUCKET_SIZE - @BOTTOM_CORRECTION*3
    else
      @index.push $(window).height() + @BOTTOM_CORRECTION
      @index.push $(window).height() + @BOTTOM_CORRECTION

    # Calculate the total count for each bucket (without replies) and the
    # maximum count.
    max = 0
    for b in @buckets
      info = b.reduce (info, a) ->
        subtotal = a.reply_count or 0
        return {
          top: info.top + 1
          replies: info.replies + subtotal
          total : info.total + subtotal + 1
        }
      ,
        top: 0
        replies: 0
        total: 0
      max = Math.max max, info.total
      b.total = info.total
      b.top = info.top
      b.replies = info.replies

      # Set up displayed number in a tab.
      # Format: <top>+<replies> if this string is no longer than 4 characters
      # Otherwise display: <ŧotal>
      temp = b.top + '+' + b.replies
      b.display =  if temp.length < 5 and b.replies > 0 then temp else b.total

    # Set up the stop interpolations for data binding
    stopData = $.map @buckets, (bucket, i) =>
      x2 = if @index[i+1]? then @index[i+1] else wrapper.height()
      offsets = [@index[i], x2]
      if bucket.total
        start = @buckets[i-1]?.total and ((@buckets[i-1].total + bucket.total) / 2) or 0
        end = @buckets[i+1]?.total and ((@buckets[i+1].total + bucket.total) / 2) or 0
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
    element = d3.select(@element[0]).datum(highlights)

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

      # Creates highlights corresponding bucket when mouse is hovered
      .on 'mousemove', (bucket) =>
        highlights = wrapper.find('.annotator-hl')
        highlights.toArray().forEach (hl) =>
          if $(hl).data('annotation') in @buckets[bucket]
            $(hl).addClass('annotator-hl-active')
          else if not $(hl).hasClass('annotator-hl-temporary')
            $(hl).removeClass('annotator-hl-active')

      # Gets rid of them after
      .on 'mouseout', =>
        highlights = wrapper.find('.annotator-hl')
        highlights.removeClass('annotator-hl-active')

      # Does one of a few things when a tab is clicked depending on type
      .on 'click', (bucket) =>
        d3.event.stopPropagation()
        highlights = wrapper.find('.annotator-hl')
        pad = defaultView.innerHeight * .2

        # If it's the upper tab, scroll to next bucket above
        if @isUpper bucket
          threshold = defaultView.pageYOffset
          {next} = highlights.toArray().reduce (acc, hl) ->
            {pos, next} = acc
            if pos < $(hl).offset().top < threshold
              pos: $(hl).offset().top
              next: $(hl)
            else
              acc
          , {pos: 0, next: null}
          next?.scrollintoview
            complete: ->
              if this.parentNode is this.ownerDocument
                scrollable = $(this.ownerDocument.body)
              else
                scrollable = $(this)
              top = scrollable.scrollTop()
              scrollable.stop().animate {scrollTop: top - pad}, 300

        # If it's the lower tab, scroll to next bucket below
        else if @isLower bucket
          threshold = defaultView.pageYOffset + defaultView.innerHeight - pad
          {next} = highlights.toArray().reduce (acc, hl) ->
            {pos, next} = acc
            if threshold < $(hl).offset().top < pos
              pos: $(hl).offset().top
              next: $(hl)
            else
              acc
          , {pos: Number.MAX_VALUE, next: null}
          next?.scrollintoview
            complete: ->
              if this.parentNode is this.ownerDocument
                scrollable = $(this.ownerDocument.body)
              else
                scrollable = $(this)
              top = scrollable.scrollTop()
              scrollable.stop().animate {scrollTop: top + pad}, 300

        # If it's neither of the above, load the bucket into the viewer
        else
          d3.event.stopPropagation()
          @dynamicBucket = false
          annotator.showViewer @buckets[bucket]

    tabs.exit().remove()

    tabs
    .style 'top', (d) =>
      "#{(@index[d] + @index[d+1]) / 2}px"

    .html (d) =>
      "<div class='label'>#{@buckets[d].display}</div><div class='svg'></div>"

    .classed('upper', @isUpper) 
    .classed('lower', @isLower)
    .classed('commenter', @isComment)

    .style 'display', (d) =>
      if (@buckets[d].length is 0) then 'none' else ''

    if @dynamicBucket
      this._fillDynamicBucket()

  _fillDynamicBucket: =>
    top = window.pageYOffset
    bottom = top + $(window).innerHeight()
    highlights = @annotator.wrapper.find('.annotator-hl')
    visible = highlights.toArray().reduce (acc, hl) =>
      if $(hl).offset().top >= top and $(hl).offset().top <= bottom
        if $(hl).data('annotation') not in acc
          acc.push $(hl).data('annotation')
      acc
    , []
    $.merge visible, @annotator.comments
    @annotator.updateViewer visible

  isUpper:   (i) => i == 1
  isLower:   (i) => i == @index.length - 3
  isComment: (i) => i == @index.length - 2
