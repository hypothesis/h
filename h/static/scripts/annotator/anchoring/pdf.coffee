seek = require('dom-seek')

Annotator = require('annotator')
xpathRange = Annotator.Range

html = require('./html')
{TextPositionAnchor, TextQuoteAnchor} = require('./types')


# Caches for performance
pageTextCache = {}
quotePositionCache = {}


getSiblingIndex = (node) ->
  siblings = Array.prototype.slice.call(node.parentNode.childNodes)
  return siblings.indexOf(node)


getNodeTextLayer = (node) ->
  until node.classList?.contains('page')
    node = node.parentNode
  return node.getElementsByClassName('textLayer')[0]


getPage = (pageIndex) ->
  return PDFViewerApplication.pdfViewer.getPageView(pageIndex)


getPageTextContent = (pageIndex) ->
  if pageTextCache[pageIndex]?
    return Promise.resolve(pageTextCache[pageIndex])
  else
    joinItems = ({items}) ->
      # Skip empty items since PDF-js leaves their text layer divs blank.
      # Excluding them makes our measurements match the rendered text layer.
      # Otherwise, the selectors we generate would not match this stored text.
      # See the appendText method of TextLayerBuilder in pdf.js.
      nonEmpty = (item.str for item in items when /\S/.test(item.str))
      textContent = nonEmpty.join('')
      pageTextCache[pageIndex] = textContent
      return textContent

    return PDFViewerApplication.pdfViewer.getPageTextContent(pageIndex)
    .then(joinItems)


getPageOffset = (pageIndex) ->
  index = -1

  next = (offset) ->
    if ++index is pageIndex
      return Promise.resolve(offset)

    return getPageTextContent(index)
    .then((textContent) -> next(offset + textContent.length))

  return next(0)


findPage = (offset) ->
  index = 0
  total = 0

  count = (textContent) ->
    if total + textContent.length >= offset
      offset = total
      return Promise.resolve({index, offset, textContent})
    else
      index++
      total += textContent.length
      return getPageTextContent(index).then(count)

  return getPageTextContent(0).then(count)


# Search for a position anchor within a page, creating a placeholder and
# anchoring to that if the page is not rendered.
anchorByPosition = (page, anchor, options) ->
  renderingState = page.renderingState
  renderingDone = page.textLayer?.renderingDone
  if renderingState is RenderingStates.FINISHED and renderingDone
    root = page.textLayer.textLayerDiv
    selector = anchor.toSelector(options)
    return html.anchor(root, [selector])
  else
    div = page.div ? page.el
    placeholder = div.getElementsByClassName('annotator-placeholder')[0]
    unless placeholder?
      placeholder = document.createElement('span')
      placeholder.classList.add('annotator-placeholder')
      placeholder.textContent = 'Loading annotations…'
      div.appendChild(placeholder)
    range = document.createRange()
    range.setStartBefore(placeholder)
    range.setEndAfter(placeholder)
    return range


# Search for a quote (with optional position hint) in the given pages.
findInPages = ([pageIndex, rest...], quote, position) ->
  unless pageIndex?
    return Promise.reject('quote not found')

  attempt = (info) ->
    # Try to find the quote in the current page.
    [page, content, offset] = info
    root = {textContent: content}
    anchor = new TextQuoteAnchor.fromSelector(root, quote)
    if position?
      hint = position.start - offset
      hint = Math.max(0, hint)
      hint = Math.min(hint, content.length)
      return anchor.toPositionAnchor({hint})
    else
      return anchor.toPositionAnchor()

  next = ->
    return findInPages(rest, quote, position)

  cacheAndFinish = (anchor) ->
    quotePositionCache[quote.exact] ?= {}
    quotePositionCache[quote.exact][position.start] = {page, anchor}
    return anchorByPosition(page, anchor)

  page = getPage(pageIndex)
  content = getPageTextContent(pageIndex)
  offset = getPageOffset(pageIndex)

  return Promise.all([page, content, offset])
  .then(attempt, next)
  .then(cacheAndFinish)


# When a position anchor is available, quote search can prioritize pages by
# the position, searching pages outward starting from the page containing the
# expected offset. This should speed up anchoring by searching fewer pages.
prioritizePages = (position) ->
  {pagesCount} = PDFViewerApplication.pdfViewer
  pageIndices = [0...pagesCount]

  sort = (pageIndex) ->
    left = pageIndices.slice(0, pageIndex)
    right = pageIndices.slice(pageIndex)
    result = []
    while left.length or right.length
      if right.length
        result.push(right.shift())
      if left.length
        result.push(left.pop())
    return result

  if position?
    return findPage(position.start)
    .then(({index}) -> return sort(index))
  else
    return Promise.resolve(pageIndices)


###*
# Anchor a set of selectors.
#
# This function converts a set of selectors into a document range.
# It encapsulates the core anchoring algorithm, using the selectors alone or
# in combination to establish the best anchor within the document.
#
# :param Element root: The root element of the anchoring context.
# :param Array selectors: The selectors to try.
# :param Object options: Options to pass to the anchor implementations.
# :return: A Promise that resolves to a Range on success.
# :rtype: Promise
####
exports.anchor = (root, selectors, options = {}) ->
  # Selectors
  position = null
  quote = null

  # Collect all the selectors
  for selector in selectors ? []
    switch selector.type
      when 'TextPositionSelector'
        position = selector
      when 'TextQuoteSelector'
        quote = selector

  # Until we successfully anchor, we fail.
  promise = Promise.reject('unable to anchor')

  # Assert the quote matches the stored quote, if applicable
  assertQuote = (range) ->
    if quote?.exact? and range.toString() != quote.exact
      throw new Error('quote mismatch')
    else
      return range

  if position?
    promise = promise.catch ->
      return findPage(position.start)
      .then ({index, offset, textContent}) ->
        page = getPage(index)
        start = position.start - offset
        end = position.end - offset
        length = end - start
        assertQuote(textContent.substr(start, length))
        anchor = new TextPositionAnchor(root, start, end)
        return anchorByPosition(page, anchor, options)

  if quote?
    promise = promise.catch ->
      if position? and quotePositionCache[quote.exact]?[position.start]?
        {page, anchor} = quotePositionCache[quote.exact][position.start]
        return anchorByPosition(page, anchor, options)

      return prioritizePages(position)
      .then((pageIndices) -> findInPages(pageIndices, quote, position))

  return promise


exports.describe = (root, range, options = {}) ->
  range = new xpathRange.BrowserRange(range).normalize()

  startTextLayer = getNodeTextLayer(range.start)
  endTextLayer = getNodeTextLayer(range.end)

  # XXX: range covers only one page
  if startTextLayer isnt endTextLayer
    throw new Error('selecting across page breaks is not supported')

  startRange = range.limit(startTextLayer)
  endRange = range.limit(endTextLayer)

  startPageIndex = getSiblingIndex(startTextLayer.parentNode)
  endPageIndex = getSiblingIndex(endTextLayer.parentNode)

  iter = document.createNodeIterator(startTextLayer, NodeFilter.SHOW_TEXT)

  start = seek(iter, range.start)
  end = seek(iter, range.end) + start + range.end.textContent.length

  return getPageOffset(startPageIndex).then (pageOffset) ->
    # XXX: range covers only one page
    start += pageOffset
    end += pageOffset

    position = new TextPositionAnchor(root, start, end).toSelector(options)

    r = document.createRange()
    r.setStartBefore(startRange.start)
    r.setEndAfter(endRange.end)

    quote = TextQuoteAnchor.fromRange(root, r, options).toSelector(options)

    return Promise.all([position, quote])


exports.purgeCache = ->
  pageTextCache = {}
  quotePositionCache = {}
