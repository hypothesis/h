$ = Annotator.$

class Annotator.Toolbar extends Annotator.Widget
  html: '<div class="annotator-toolbar"></div>'

  options:
    items: [
      "title": "Show Annotations"
      "class": "alwaysonhighlights-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        state = not window.annotator.alwaysOnMode
        window.annotator.alwaysOnMode = state
        window.annotator.setPersistentHighlights()
        if state
          $(event.target).addClass('pushed')
        else
          $(event.target).removeClass('pushed')
    ,
      "title": "Highlighting Mode"
      "class": "highlighter-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        state = not window.annotator.highlightingMode
        window.annotator.highlightingMode = state
        window.annotator.setPersistentHighlights()
        if state
          $(event.target).addClass('pushed')
        else
          $(event.target).removeClass('pushed')
    ,
      "title": "New Comment"
      "class": "commenter-icon"
      "click": (event) ->
        event.preventDefault()
        event.stopPropagation()
        window.annotator.addComment()
    ]

  constructor: (options) ->
    super $(@html)[0], options
    @buttons = @options.items.reduce  (buttons, item) =>
      button = $('<a></a>')
      .attr('href', '')
      .attr('title', item.title)
      .on('click', item.click)
      .addClass(item.class)
      .data('state', false)
      buttons.add button
    , $()
    @element
    .append(@buttons)
    .wrapInner('<ul></ul>')
    @buttons.wrap('<li></li>')

  show: ->
    @element.removeClass @classes.hide
    this

  hide: ->
    @element.addClass @classes.hide
    this
