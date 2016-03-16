Annotator = require('annotator')
queryString = require('query-string')
$ = Annotator.$

Guest = require('./guest')

module.exports = class Host extends Guest
  constructor: (element, options) ->
    appOpts = queryString.stringify(
      Object.assign({}, options, {app: undefined})
    )
    options.app += (if '?' in options.app then '&' else '?') + appOpts

    # Create the iframe
    app = $('<iframe></iframe>')
    .attr('name', 'hyp_sidebar_frame')
    # enable media in annotations to be shown fullscreen
    .attr('allowfullscreen', '')
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
      if options.showHighlights == undefined
        # Highlights are on by default.
        options.showHighlights = true
      this.setVisibleHighlights(options.showHighlights)

      # Show the UI
      @frame.css('display', '')

    this.on 'beforeAnnotationCreated', (annotation) ->
      # When a new non-highlight annotation is created, focus
      # the sidebar so that the text editor can be focused as
      # soon as the annotation card appears
      if !annotation.$highlight
        app[0].contentWindow.focus()

  destroy: ->
    @frame.remove()
    super
