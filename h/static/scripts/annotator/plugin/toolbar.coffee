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

  touch = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

  events:
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html: '<div class="annotator-toolbar"></div>'

  pluginInit: ->
    @annotator.toolbar = @toolbar = $(@html)
    if touch
      # When there is a selection on touch devices show/hide highlighter
      document.addEventListener "selectstart", =>
        if window.getSelection().toString() != ""
          this.showHighlightButton(false)
        else
          this.showHighlightButton(true)
    if @options.container?
      $(@options.container).append @toolbar
    else
      $(@element).append @toolbar

    items = [
      "title": "Toggle Sidebar"
      "class": "annotator-toolbar-toggle h-icon-chevron-left"
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
      "title": "Toggle Highlight Visibility"
      "class": "h-icon-visibility"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          state = not @annotator.visibleHighlights
          @annotator.setVisibleHighlights state
    ,
      "title": "New Note"
      "class": "h-icon-insert-comment"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          event.target.dataset.action = "comment"
          @annotator.onAdderClick(event)
    ,
      "title": "Highlight"
      "class": "h-icon-border-color"
      "on":
        "click": (event) =>
          event.preventDefault()
          event.stopPropagation()
          @annotator.onAdderClick target: dataset: action: "highlight"
          this.showHighlightButton(false)
    ]
    @buttons = $(makeButton(item) for item in items)
    list = $('<ul></ul>')
    @buttons.appendTo(list)
    @toolbar.append(list)

    # Hide highlight button.
    $(@buttons[3]).hide()

    # Remove focus from the anchors when clicked, this removes the focus
    # styles intended only for keyboard navigation. IE/FF apply the focus
    # psuedo-class to a clicked element.
    @toolbar.on('mouseup', 'a', (event) -> $(event.target).blur())
    this._updateStickyButtons()

  showHighlightButton: (state)->
    if state
      $(@buttons[3]).show()
    else
      $(@buttons[3]).hide()
    this._updateStickyButtons()

  onSetVisibleHighlights: (state) ->
    if state
      $(@buttons[1]).children().removeClass('h-icon-visibility-off')
      $(@buttons[1]).children().addClass('h-icon-visibility')
    else
      $(@buttons[1]).children().removeClass('h-icon-visibility')
      $(@buttons[1]).children().addClass('h-icon-visibility-off')

  _updateStickyButtons: ->
    # The highlight button is hidden except when there is a selection on touch devices
    if $(@buttons[3]).css('display') == 'none'
      height = 105
    else height = 140
    this.toolbar.css("min-height", "#{height}px")
    this.annotator.plugins.BucketBar?.BUCKET_THRESHOLD_PAD = height
    this.annotator.plugins.BucketBar?._update()
