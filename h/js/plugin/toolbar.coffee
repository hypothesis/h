$ = Annotator.$

class Annotator.Plugin.Toolbar extends Annotator.Plugin
  events:
    '.annotator-toolbar li:first-child mouseenter': 'show'
    '.annotator-toolbar mouseleave': 'hide'
    'updateNotificationCounter': 'onUpdateNotificationCounter'
    'setTool': 'onSetTool'
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html:
    element: '<div class="annotator-toolbar annotator-hide"></div>'
    notification: '<div class="annotator-notification-counter"></div>'

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
    @annotator.toolbar = @toolbar = $(@html.element)
    if @options.container?
      $(@options.container).append @toolbar
    else
      $(@element).append @toolbar

    @notificationCounter = $(@html.notification)
    @toolbar.append(@notificationCounter)

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

  onUpdateNotificationCounter: (count) ->
    element = $(@buttons[0])
    element.toggle('fg_highlight', {color: 'lightblue'})
    setTimeout ->
      element.toggle('fg_highlight', {color: 'lightblue'})
    , 500

    switch
      when count > 9
        @notificationCounter.text('>9')
      when 0 < count <= 9
        @notificationCounter.text("+#{count}")
      else
        @notificationCounter.text('')

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
      height = (count + 1) * 32  # +1 -- top button is always visible
      this.toolbar.css("min-height", "#{height}px")
    else
      height = 32
      this.toolbar.css("min-height", "")
    this.annotator.plugins.Heatmap?.BUCKET_THRESHOLD_PAD = height - 5
    this.annotator.plugins.Heatmap?._update();