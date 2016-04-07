Annotator = require('annotator')
$ = Annotator.$


# This plugin implements the UI code for creating text annotations
module.exports = class TextSelection extends Annotator.Plugin

  pluginInit: ->
    # Register the event handlers required for creating a selection
    $(document).bind({
      "touchend": @checkForEndSelection
      "mouseup": @checkForEndSelection
      "ready": @checkForEndSelection
    })

    null

  destroy: ->
    $(document).unbind({
      "touchend": @checkForEndSelection
      "mouseup": @checkForEndSelection
      "ready": @checkForEndSelection
    })
    super

  # This is called when the mouse is released.
  # Checks to see if a selection  been made on mouseup and if so,
  # calls Annotator's onSuccessfulSelection method.
  #
  # event - The event triggered this. Usually it's a mouseup Event,
  #         but that's not necessary.
  #
  # Returns nothing.
  checkForEndSelection: (event = {}) =>
    callback = ->
      # Get the currently selected ranges.
      selection = Annotator.Util.getGlobal().getSelection()
      ranges = for i in [0...selection.rangeCount]
        r = selection.getRangeAt(0)
        if r.collapsed then continue else r

      if ranges.length
        event.ranges = ranges
        @annotator.onSuccessfulSelection event
      else
        @annotator.onFailedSelection event

    # Run callback after the current event loop tick
    # so that the mouseup event can update the document selection.
    setTimeout callback, 0
