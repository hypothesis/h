Annotator = require('annotator')
$ = Annotator.$

Guest = require('./guest')


module.exports = class Host extends Guest
  constructor: (element, options) ->
    if options.firstRun
      options.app += (if '?' in options.app then '&' else '?') + 'firstrun'

    # Create the iframe
    app = $('<iframe></iframe>')
    .attr('name', 'hyp_sidebar_frame')
    .attr('seamless', '')
    .attr('src', options.app)

    @frame = $('<div></div>')
    .css('display', 'none')
    .addClass('annotator-frame annotator-outer')
    .appendTo(element)

    super

    app.appendTo(@frame)

    this.on 'panelReady', =>
      # Initialize tool state.
      this.setVisibleHighlights(!!options.showHighlights)

      # Show the UI
      @frame.css('display', '')

  destroy: ->
    @frame.remove()
    super
