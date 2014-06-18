$ = Annotator.$

class Annotator.Plugin.Heatmap extends Annotator.Plugin
  # prototype constants
  BUCKET_THRESHOLD_PAD: 30
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
  dynamicBucket: false

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
          this._scheduleUpdate()
      else
        @annotator.subscribe event, this._scheduleUpdate

    @element.on 'click', (event) =>
      event.stopPropagation()
      @dynamicBucket = true
      @annotator.showViewer "Screen", this._getDynamicBucket()

    @element.on 'mouseup', (event) =>
      event.stopPropagation()

    $(window).on 'resize scroll', this._update
    $(document.body).on 'resize scroll', '*', this._update

    # Event handler to finish scrolling when we have to
    # wait for anchors to be realized
    @annotator.subscribe "highlightsCreated", (highlights) =>
      # All the highlights are guaranteed to belong to one anchor,
      # so we can do this:
      anchor = if Array.isArray highlights # Did we got a list ?
        highlights[0].anchor
      else
        # I see that somehow if I publish an array with a signel element,
        # by the time it arrives, it's not an array any more.
        # Weird, but for now, let's work around it.
        highlights.anchor
      if anchor.annotation.id? # Is this a finished annotation ?
        @_scheduleUpdate()

      if @pendingScroll? and anchor in @pendingScroll.anchors
        # One of the wanted anchors has been realized
        unless --@pendingScroll.count
          # All anchors have been realized
          page = @pendingScroll.page
          dir = if @pendingScroll.direction is "up" then +1 else -1
          {next} = @pendingScroll.anchors.reduce (acc, anchor) ->
            {start, next} = acc
            hl = anchor.highlight[page]
            if not next? or hl.getTop()*dir > start*dir
              start: hl.getTop()
              next: hl
            else
              acc
          , {}

          next.paddedScrollDownTo()
          delete @pendingScroll

    @annotator.subscribe "highlightRemoved", (highlight) =>
      if highlight.annotation.id? # Is this a finished annotation ?
        @_scheduleUpdate()

    addEventListener "docPageScrolling", => @_update()

  # Update the heatmap sometimes soon
  _scheduleUpdate: =>
    return if @_updatePending
    @_updatePending = true
    setTimeout ( =>
      delete @_updatePending
      @_update()
    ), 200

  _maybeRebaseUrls: ->
    # We can't rely on browsers to implement the xml:base property correctly.
    # Therefore, we must rebase the fragment references we use in the SVG for
    # the heatmap in case the page contains a <base> tag which might otherwise
    # break these references.

    return unless document.getElementsByTagName('base').length

    loc = window.location
    base = "#{loc.protocol}//#{loc.host}#{loc.pathname}#{loc.search}"

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

  _collectVirtualAnnotations: (startPage, endPage) ->
    results = []
    for page in [startPage .. endPage]
      anchors = @annotator.anchors[page]
      if anchors?
        $.merge results, (anchor.annotation for anchor in anchors when not anchor.fullyRealized)
    results

  # Find the first/last annotation from the list, based on page number,
  # and Y offset, if already known, and jump to it.
  # If the Y offsets are not yet known, just jump the page,
  # wait for the highlights to be realized, and finish the selection then.
  _jumpMinMax: (annotations, direction) ->
    unless direction in ["up", "down"]
      throw "Direction is mandatory!"
    dir = if direction is "up" then +1 else -1
    {next} = annotations.reduce (acc, ann) ->
      {start, next} = acc
      anchor = ann.anchors[0]
      if not next? or start.page*dir < anchor.startPage*dir
        # This one is obviously better
        #console.log "Found anchor on better page."
        start:
          page: anchor.startPage
          top: anchor.highlight[anchor.startPage]?.getTop()
        next: [anchor]
      else if start.page is anchor.startPage
        # This is on the same page, might be better
        hl = anchor.highlight[start.page]
        if hl?
          # We have a real highlight, let's compare coordinates
          if start.top*dir < hl.getTop()*dir
            #console.log "Found anchor on same page, better pos."
            # OK, this one is better
            start:
              page: start.page
              top: hl.getTop()
            next: [anchor]
          else
            # No, let's keep the old one instead
            #console.log "Found anchor on same page, worse pos. (Known: ", start.top, "; found: ", hl.getTop(), ")"
            acc
        else
          # The page is not yet rendered, can't decide yet.
          # Let's just store this one, too
          #console.log "Found anchor on same page, unknown pos."
          start: page: start.page
          next: $.merge next, [anchor]
      else
        # No, we have clearly seen better alternatives
        acc
    , {}
    #console.log "Next is", next

    # Get an anchor from the page we want to go to
    anchor = next[0]
    startPage = anchor.startPage

    # Is this rendered?
    if @annotator.domMapper.isPageMapped startPage
      # If it was rendered, then we only have one result. Go there.
      hl = anchor.highlight[startPage]
      hl.paddedScrollTo direction
    else
      # Not rendered yet. Go to the page, and see what happens.
      @pendingScroll =
        anchors: next
        count: next.length
        page: startPage
        direction: direction
      @annotator.domMapper.setPageIndex startPage

  _update: =>
    wrapper = @annotator.wrapper
    highlights = @annotator.getHighlights()
    defaultView = wrapper[0].ownerDocument.defaultView

    # Keep track of buckets of annotations above and below the viewport
    above = []
    below = []

    # Get the page numbers
    mapper = @annotator.domMapper
    firstPage = 0
    currentPage = mapper.getPageIndex()
    lastPage = mapper.getPageCount() - 1

    # Collect the virtual anchors from above and below
    $.merge above, this._collectVirtualAnnotations 0, currentPage-1
    $.merge below, this._collectVirtualAnnotations currentPage+1, lastPage

    comments = @annotator.comments.slice()

    # Construct control points for the heatmap
    points = highlights.reduce (points, hl, i) =>
      d = hl.annotation
      x = hl.getTop() - defaultView.pageYOffset
      h = hl.getHeight()

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
          replies: (info.replies or 0) + subtotal
          total : (info.total or 0) + subtotal + 1
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
    element = d3.select(@element[0])

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
      @bucketIndices = buckets
      buckets

    tabs.enter().append('div')
      .classed('heatmap-pointer', true)

      # Creates highlights corresponding bucket when mouse is hovered
      .on 'mousemove', (bucket) =>
        for hl in @annotator.getHighlights()
          if hl.annotation in @buckets[bucket]
            hl.setActive true, true
          else
            unless hl.isTemporary()
              hl.setActive false, true
        @annotator.publish "finalizeHighlights"

      # Gets rid of them after
      .on 'mouseout', =>
        for hl in @annotator.getHighlights()
          unless hl.isTemporary()
            hl.setActive false, true
        @annotator.publish "finalizeHighlights"

      # Does one of a few things when a tab is clicked depending on type
      .on 'click', (bucket) =>
        d3.event.stopPropagation()
        pad = defaultView.innerHeight * .2

        # If it's the upper tab, scroll to next anchor above
        if (@isUpper bucket)
          @dynamicBucket = true
          @_jumpMinMax @buckets[bucket], "up"
        # If it's the lower tab, scroll to next anchor below
        else if (@isLower bucket)
          @dynamicBucket = true
          @_jumpMinMax @buckets[bucket], "down"
        else if (@isComment bucket)
          @commentClick()
        else
          d3.event.stopPropagation()
          annotations = @buckets[bucket].slice()
          annotator.selectAnnotations annotations,
            (d3.event.ctrlKey or d3.event.metaKey),
            (annotations.length is 1) # Only focus if there is only one

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
      @annotator.updateViewer "Screen", this._getDynamicBucket()

    @tabs = tabs

  _getDynamicBucket: ->
    top = window.pageYOffset
    bottom = top + $(window).innerHeight()
    anchors = @annotator.getHighlights()
    visible = anchors.reduce (acc, hl) =>
      if top <= hl.getTop() <= bottom
        if hl.annotation not in acc
          acc.push hl.annotation
      acc
    , []

  _getCommentBucket: => @index.length - 2

  blinkBuckets: =>
    for tab, index in @tabs[0]
      bucket = @buckets[@bucketIndices[index]]

      hasUpdate = false
      for annotation in bucket
        if annotation._updatedAnnotation?
          hasUpdate = true
          delete annotation._updatedAnnotation

      unless hasUpdate then continue
      element = $(tab)
      element.toggle('fg_highlight', {color: 'lightblue'})
      setTimeout ->
        element.toggle('fg_highlight', {color: 'lightblue'})
      , 500

  isUpper:   (i) => i == 1
  isLower:   (i) => i == @index.length - 3
  isComment: (i) => i is @_getCommentBucket()

  # Simulate clicking on the comments tab
  commentClick: =>
    @dynamicBucket = false
    annotator.showViewer "Comments", @buckets[@_getCommentBucket()]
