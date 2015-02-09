$ = Annotator.$

makeButton = (item) ->
  anchor = $('<a></a>')
  .attr('href', '')
  .attr('title', item.title)
  .on(item.on)
  .addClass(item.class)
  button = $('<li></li>').append(anchor)
  return button[0]

class Annotator.Plugin.Toolbar extends Annotator.Plugin
  PUSHED_CLASS = 'annotator-pushed'

  events:
    '.annotator-toolbar mouseenter': 'show'
    '.annotator-toolbar mouseleave': 'hide'
    'setTool': 'onSetTool'
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html: '<div class="annotator-toolbar annotator-hide"></div>'

  pluginInit: ->
    @annotator.toolbar = @toolbar = $(@html)
    if @options.container?
      $(@options.container).append @toolbar
    else
      $(@element).append @toolbar

    items = [
      "title": "Toggle Sidebar"
      "class": "annotator-toolbar-toggle h-icon-comment"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          collapsed = @annotator.frame.hasClass('annotator-collapsed')
          if collapsed
            @annotator.triggerShowFrame()
          else
            @annotator.triggerHideFrame()
    ,
      "title": "Show Annotations"
      "class": "h-icon-visible"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          state = not @annotator.visibleHighlights
          @annotator.setVisibleHighlights state
    ,
      "title": "Highlighting Mode"
      "class": "h-icon-highlighter"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          state = not (@annotator.tool is 'highlight')
          tool = if state then 'highlight' else 'comment'
          @annotator.setTool tool
    ,
      "title": "New Comment"
      "class": "h-icon-plus"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          @annotator.addComment()
    ]
    @buttons = $(makeButton(item) for item in items)

    list = $('<ul></ul>')
    @buttons.appendTo(list)
    @toolbar.append(list)

    # Remove focus from the anchors when clicked, this removes the focus
    # styles intended only for keyboard navigation. IE/FF apply the focus
    # psuedo-class to a clicked element.
    @toolbar.on('mouseup', 'a', (event) -> $(event.target).blur())

  show: -> this.toolbar.removeClass('annotator-hide')

  hide: -> this.toolbar.addClass('annotator-hide')

  onSetTool: (name) ->
    if name is 'highlight'
      $(@buttons[2]).addClass(PUSHED_CLASS)
    else
      $(@buttons[2]).removeClass(PUSHED_CLASS)
    this._updateStickyButtons()

  onSetVisibleHighlights: (state) ->
    if state
      $(@buttons[1]).addClass(PUSHED_CLASS)
    else
      $(@buttons[1]).removeClass(PUSHED_CLASS)
    this._updateStickyButtons()

  _updateStickyButtons: ->
    count = $(@buttons).filter(-> $(this).hasClass(PUSHED_CLASS)).length
    if count
      height = (count + 1) * 35  # +1 -- top button is always visible
      this.toolbar.css("min-height", "#{height}px")
    else
      height = 35
      this.toolbar.css("min-height", "")
    this.annotator.plugins.BucketBar?.BUCKET_THRESHOLD_PAD = height
    this.annotator.plugins.BucketBar?._update()
