$ = Annotator.$

class Annotator.Plugin.Toolbar extends Annotator.Plugin
  PUSHED_CLASS = 'annotator-pushed'

  events:
    '.annotator-toolbar mouseenter': 'show'
    '.annotator-toolbar mouseleave': 'hide'
    'setTool': 'onSetTool'
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html: '<div class="annotator-toolbar annotator-hide"></div>'

  options:
    items: [
      "title": "Toggle Sidebar"
      "class": "annotator-toolbar-toggle h-icon-comment"
      "on":
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          collapsed = window.annotator.frame.hasClass('annotator-collapsed')
          if collapsed
            window.annotator.showFrame()
          else
            window.annotator.hideFrame()
        # Remove focus from the anchor when clicked, this removes the focus
        # styles intended only for keyboard navigation. IE/FF apply the focus
        # psuedo-class to a clicked element.
        "mouseup": (event) -> $(event.target).blur()
    ,
      "title": "Show Annotations"
      "class": "h-icon-visible"
      "on":
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          state = not window.annotator.visibleHighlights
          window.annotator.setVisibleHighlights state
    ,
      "title": "Highlighting Mode"
      "class": "h-icon-highlighter"
      "on":
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          state = not (window.annotator.tool is 'highlight')
          tool = if state then 'highlight' else 'comment'
          window.annotator.setTool tool
    ,
      "title": "New Comment"
      "class": "h-icon-plus"
      "on":
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          window.annotator.addComment()
    ]

  pluginInit: ->
    @annotator.toolbar = @toolbar = $(@html)
    if @options.container?
      $(@options.container).append @toolbar
    else
      $(@element).append @toolbar

    @buttons = @options.items.reduce  (buttons, item) =>
      anchor = $('<a></a>')
      .attr('href', '')
      .attr('title', item.title)
      .on(item.on)
      .addClass(item.class)
      button = $('<li></li>').append(anchor)
      buttons.add button
    , $()

    list = $('<ul></ul>')
    @buttons.appendTo(list)
    @toolbar.append(list)

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
    this.annotator.plugins.Heatmap?.BUCKET_THRESHOLD_PAD = height
    this.annotator.plugins.Heatmap?._update();
