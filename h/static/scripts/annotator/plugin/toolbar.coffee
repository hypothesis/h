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
  events:
    'setVisibleHighlights': 'onSetVisibleHighlights'

  html: '<div class="annotator-toolbar"></div>'

  pluginInit: ->
    @annotator.toolbar = @toolbar = $(@html)
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
      "title": "Hide Highlights"
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
          @annotator.onAdderClick target: dataset: action: "comment"
    ]
    @buttons = $(makeButton(item) for item in items)

    list = $('<ul></ul>')
    @buttons.appendTo(list)
    @toolbar.append(list)

    # Remove focus from the anchors when clicked, this removes the focus
    # styles intended only for keyboard navigation. IE/FF apply the focus
    # psuedo-class to a clicked element.
    @toolbar.on('mouseup', 'a', (event) -> $(event.target).blur())

  onSetVisibleHighlights: (state) ->
    if state
      $(@buttons[1]).children().removeClass('h-icon-visibility-off')
      $(@buttons[1]).children().addClass('h-icon-visibility')
      $(@buttons[1]).children().prop('title', 'Hide Highlights');
    else
      $(@buttons[1]).children().removeClass('h-icon-visibility')
      $(@buttons[1]).children().addClass('h-icon-visibility-off')
      $(@buttons[1]).children().prop('title', 'Show Highlights');

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
