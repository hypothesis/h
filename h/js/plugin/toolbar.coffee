$ = Annotator.$

class Annotator.Plugin.Toolbar extends Annotator.Plugin
  events:
    'updateNotificationCounter': 'onUpdateNotificationCounter'
    'setTool': 'onSetTool'
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html:
    element: '<div class="annotator-toolbar"></div>'
    notification: '<div class="annotator-notification-counter"></div>'
    stickybuttons: '<div class="stickybuttons"></div>'

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
        if state
          $(event.target).addClass('pushed')
          $(".stickybuttons").show()
          $(".stickybuttons").removeClass('stickybuttons2')
          if window.annotator.tool is 'highlight'
            $(".stickybuttons").addClass('stickybuttons2')
          $("#sticky1").parent().show()
        else
          $(event.target).removeClass('pushed')
          $("#sticky1").parent().hide()
          if not (window.annotator.tool is 'highlight')
            $(".stickybuttons").hide()
        window.annotator.plugins.Heatmap._update()
    ,
      "title": "Highlighting Mode"
      "class": "highlighter-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        state = not (window.annotator.tool is 'highlight')
        tool = if state then 'highlight' else 'comment'
        window.annotator.setTool tool
        $(".stickybuttons").removeClass('stickybuttons2')
        if state
          $(event.target).addClass('pushed')
          $(".stickybuttons").show()
          if window.annotator.visibleHighlights
            $(".stickybuttons").addClass('stickybuttons2')
          $("#sticky2").parent().show()
        else
          $(event.target).removeClass('pushed')
          $("#sticky2").parent().hide()
          if not window.annotator.visibleHighlights
            $(".stickybuttons").hide()
        window.annotator.plugins.Heatmap._update()
    ,
      "title": "New Comment"
      "class": "commenter-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        window.annotator.addComment()
    ]

    stickyoptions:
      items: [
        "title": "Show Annotations"
        "class": "alwaysonhighlights-icon"
        "id"   : "sticky1"
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          $(event.target).parent().hide()
          state = not window.annotator.visibleHighlights
          window.annotator.setVisibleHighlights state
          $(".stickybuttons").removeClass('stickybuttons2')
          $(".alwaysonhighlights-icon").removeClass('pushed')
          if not (window.annotator.tool is 'highlight')
            $(".stickybuttons").hide()
          window.annotator.plugins.Heatmap._update()
      ,
        "title": "Highlighting Mode"
        "class": "highlighter-icon"
        "id"   : "sticky2"
        "click": (event) ->
          event.preventDefault()
          event.stopPropagation()
          $(event.target).parent().hide()
          state = not (window.annotator.tool is 'highlight')
          tool = if state then 'highlight' else 'comment'
          window.annotator.setTool tool
          $(".stickybuttons").removeClass('stickybuttons2')
          $(".highlighter-icon").removeClass('pushed')
          if not window.annotator.visibleHighlights
            $(".stickybuttons").hide()
          window.annotator.plugins.Heatmap._update()
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
      button = $('<a></a>')
      .attr('href', '')
      .attr('title', item.title)
      .on('click', item.click)
      .addClass(item.class)
      .data('state', false)
      buttons.add button
    , $()

    list = $('<ul></ul>')
    @buttons.appendTo(list)
    @buttons.wrap('<li></li>')
    @toolbar.append(list)

    # STICKY BUTTONS
    @sticky = $(@html.stickybuttons)
    if @options.container?
      $(@options.container).append @sticky
    else
      $(@element).append(@sticky)
  
    @stickybuttons = @options.stickyoptions.items.reduce  (buttons, item) =>
      stickybutton = $('<a></a>')
      .attr('href', '')
      .attr('title', item.title)
      .attr('id', item.id)
      .on('click', item.click)
      .addClass(item.class)
      .data('state', false)
      buttons.add stickybutton
    , $()

    list = $('<ul></ul>')
    @stickybuttons.appendTo(list)
    @stickybuttons.wrap('<li></li>')
    @sticky.append(list)
    $(".stickybuttons").hide()
    $("#sticky1").parent().hide()
    $("#sticky2").parent().hide()

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

  onSetVisibleHighlights: (state) ->
    if state
      $(@buttons[1]).addClass('pushed')
    else
      $(@buttons[1]).removeClass('pushed')
