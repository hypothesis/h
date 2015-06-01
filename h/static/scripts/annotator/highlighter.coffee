Annotator = require('annotator')
$ = Annotator.$


# Public: Wraps the DOM Nodes within the provided range with a highlight
# element of the specified class and returns the highlight Elements.
#
# normedRange - A NormalizedRange to be highlighted.
# cssClass - A CSS class to use for the highlight (default: 'annotator-hl')
#
# Returns an array of highlight Elements.
exports.highlightRange = (normedRange, cssClass='annotator-hl') ->
  white = /^\s*$/

  hl = $("<span class='#{cssClass}'></span>")

  # Ignore text nodes that contain only whitespace characters. This prevents
  # spans being injected between elements that can only contain a restricted
  # subset of nodes such as table rows and lists. This does mean that there
  # may be the odd abandoned whitespace node in a paragraph that is skipped
  # but better than breaking table layouts.

  nodes = $(normedRange.textNodes()).filter((i) -> not white.test @nodeValue)
  r = nodes.wrap(hl).parent().show().toArray()


exports.removeHighlights = (highlights) ->
  for h in highlights when h.parentNode?
    $(h).replaceWith(h.childNodes)
