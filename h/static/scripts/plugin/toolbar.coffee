$ = Annotator.$

class Annotator.Plugin.Toolbar extends Annotator.Plugin
  events:
    '.annotator-toolbar mouseenter': 'show'
    '.annotator-toolbar mouseleave': 'hide'
    'setTool': 'onSetTool'
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html: '<div class="annotator-toolbar annotator-hide"></div>'

  options:
    items: [
      "title": "Toggle Sidebar"
      "class": "tri-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        collapsed = window.annotator.frame.hasClass('annotator-collapsed')
        if collapsed
          window.annotator.showFrame()
        else
          window.annotator.hideFrame()
    ,
      "title": "Show Annotations"
      "class": "alwaysonhighlights-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        state = not window.annotator.visibleHighlights
        window.annotator.setVisibleHighlights state
    ,
      "title": "Highlighting Mode"
      "class": "highlighter-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        state = not (window.annotator.tool is 'highlight')
        tool = if state then 'highlight' else 'comment'
        window.annotator.setTool tool
    ,
      "title": "New Comment"
      "class": "commenter-icon"
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
      .on('click', item.click)
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
      $(@buttons[2]).addClass('pushed')
    else
      $(@buttons[2]).removeClass('pushed')
    this._updateStickyButtons()

  onSetVisibleHighlights: (state) ->
    if state
      $(@buttons[1]).addClass('pushed')
    else
      $(@buttons[1]).removeClass('pushed')
    this._updateStickyButtons()

  _updateStickyButtons: ->
    count = $(@buttons).filter(-> $(this).hasClass('pushed')).length
    if count
      height = (count + 1) * 35  # +1 -- top button is always visible
      this.toolbar.css("min-height", "#{height}px")
    else
      height = 35
      this.toolbar.css("min-height", "")
    this.annotator.plugins.Heatmap?.BUCKET_THRESHOLD_PAD = height
    this.annotator.plugins.Heatmap?._update();
