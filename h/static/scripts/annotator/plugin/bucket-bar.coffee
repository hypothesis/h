Annotator = require('annotator')

$ = Annotator.$

class Annotator.Plugin.BucketBar extends Annotator.Plugin
  # prototype constants
  BUCKET_THRESHOLD_PAD: 30
  BUCKET_SIZE: 16

  # svg skeleton
  html: """
        <div class="annotator-bucket-bar">
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

  # tab elements
  tabs: null

  constructor: (element, options) ->
    super $(@html), options

    if @options.container?
      $(@options.container).append @element
    else
      $(element).append @element

  pluginInit: ->
    events = [
      'annotationCreated', 'annotationUpdated', 'annotationDeleted',
      'annotationsLoaded'
    ]
    for event in events
      @annotator.subscribe event, this._scheduleUpdate

    @element.on 'click', (event) =>
      event.stopPropagation()
      @annotator.showFrame()

    @element.on 'mouseup', (event) =>
      event.stopPropagation()

    $(window).on 'resize scroll', this._scheduleUpdate
    $(document.body).on 'resize scroll', '*', this._scheduleUpdate

    # Event handler to to update when new highlights have been created
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
        this._scheduleUpdate()

    # Event handler to to update when highlights have been removed
    @annotator.subscribe "highlightRemoved", (highlight) =>
      if highlight.annotation.id? # Is this a finished annotation ?
        this._scheduleUpdate()

    addEventListener "docPageScrolling", this._scheduleUpdate

  # Update sometime soon
  _scheduleUpdate: =>
    return if @_updatePending
    @_updatePending = true
    setTimeout =>
      delete @_updatePending
      @_update()
    , 60 / 1000

  _collate: (a, b) ->
    for i in [0..a.length-1]
      if a[i] < b[i]
        return -1
      if a[i] > b[i]
        return 1
    return 0

  _collectVirtualAnnotations: (startPage, endPage) ->
    results = []
    for page in [startPage .. endPage]
      anchors = @annotator.anchoring.anchors[page]
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
            # OK, this one is better
            start:
              page: start.page
              top: hl.getTop()
            next: [anchor]
          else
            # No, let's keep the old one instead
            acc
        else
          # The page is not yet rendered, can't decide yet.
          # Let's just store this one, too
          start: page: start.page
          next: $.merge next, [anchor]
      else
        # No, we have clearly seen better alternatives
        acc
    , {}

    # Get an anchor from the page we want to go to
    anchor = next[0]
    anchor.scrollToView()

  _update: =>
    wrapper = @annotator.wrapper
    highlights = @annotator.anchoring.getHighlights()
    defaultView = wrapper[0].ownerDocument.defaultView

    # Keep track of buckets of annotations above and below the viewport
    above = []
    below = []

    # Get the page numbers
    mapper = @annotator.anchoring.document
    return unless mapper? # Maybe it's too soon to do this
    firstPage = 0
    currentPage = mapper.getPageIndex()
    lastPage = mapper.getPageCount() - 1

    # Collect the virtual anchors from above and below
    $.merge above, this._collectVirtualAnnotations 0, currentPage-1
    $.merge below, this._collectVirtualAnnotations currentPage+1, lastPage

    # Construct indicator points
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

    # Scroll up
    @buckets.unshift [], above, []
    @index.unshift 0, @BUCKET_THRESHOLD_PAD + 6,
      (@BUCKET_THRESHOLD_PAD + @BUCKET_SIZE) + 6

    # Scroll down
    @buckets.push [], below, []
    @index.push $(window).height() - @BUCKET_SIZE - 12,
      $(window).height() - @BUCKET_SIZE - 11,
      $(window).height()

    # Calculate the total count for each bucket (without replies) and the
    # maximum count.
    max = 0
    for b in @buckets
      max = Math.max max, b.length

    # Update the data bindings
    element = @element

    # Keep track of tabs to keep element creation to a minimum.
    @tabs ||= $([])

    # Remove any extra tabs and update @tabs.
    @tabs.slice(@buckets.length).remove()
    @tabs = @tabs.slice(0, @buckets.length)

    # Create any new tabs if needed.
    $.each @buckets.slice(@tabs.length), =>
      div = $('<div/>').appendTo(element)

      @tabs.push(div[0])

      div.addClass('annotator-bucket-indicator')

      # Creates highlights corresponding bucket when mouse is hovered
      # TODO: This should use event delegation on the container.
      .on 'mousemove', (event) =>
        bucket = @tabs.index(event.currentTarget)
        for hl in @annotator.anchoring.getHighlights()
          if hl.annotation in @buckets[bucket]
            hl.setFocused true
          else
            hl.setFocused false

      # Gets rid of them after
      .on 'mouseout', =>
        for hl in @annotator.anchoring.getHighlights()
          hl.setFocused false

      # Does one of a few things when a tab is clicked depending on type
      .on 'click', (event) =>
        bucket = @tabs.index(event.currentTarget)
        event.stopPropagation()
        pad = defaultView.innerHeight * .2

        # If it's the upper tab, scroll to next anchor above
        if (@isUpper bucket)
          @_jumpMinMax @buckets[bucket], "up"
        # If it's the lower tab, scroll to next anchor below
        else if (@isLower bucket)
          @_jumpMinMax @buckets[bucket], "down"
        else
          annotations = @buckets[bucket].slice()
          annotator.selectAnnotations annotations,
            (event.ctrlKey or event.metaKey),

    this._buildTabs(@tabs, @buckets)

  _buildTabs: ->
    @tabs.each (d, el) =>
      el = $(el)
      bucket = @buckets[d]
      bucketLength = bucket?.length

      title = if bucketLength != 1
        "Show #{bucketLength} annotations"
      else if bucketLength > 0
        'Show one annotation'

      el.attr('title', title)
      el.toggleClass('upper', @isUpper(d))
      el.toggleClass('lower', @isLower(d))

      el.css({
        top: (@index[d] + @index[d+1]) / 2
        marginTop: if @isUpper(d) or @isLower(d) then -9 else -8
        display: unless bucketLength then 'none' else ''
      })

      if bucket
        el.html("<div class='label'>#{bucketLength}</div>")

  isUpper:   (i) -> i == 1
  isLower:   (i) -> i == @index.length - 2

exports.BucketBar = Annotator.Plugin.BucketBar
