seek = require('dom-seek')

Annotator = require('annotator')
xpathRange = Annotator.Range

html = require('./html')
{TextPositionAnchor, TextQuoteAnchor} = require('./types')


getSiblingIndex = (node) ->
  siblings = Array.prototype.slice.call(node.parentNode.childNodes)
  return siblings.indexOf(node)


getNodeTextLayer = (node) ->
  until node.classList?.contains('page')
    node = node.parentNode
  return node.getElementsByClassName('textLayer')[0]


getPage = (pageIndex) ->
  return PDFViewerApplication.pdfViewer.pages[pageIndex]


getPageTextContent = (pageIndex) ->
  return PDFViewerApplication.pdfViewer.getPageTextContent(pageIndex)
  .then((textContent) -> (item.str for item in textContent.items).join(''))


# XXX: This will break if the viewer changes documents
_pageOffsetCache = {}

getPageOffset = (pageIndex) ->
  index = -1

  if _pageOffsetCache[pageIndex]?
    return Promise.resolve(_pageOffsetCache[pageIndex])

  next = (offset) ->
    if ++index is pageIndex
      _pageOffsetCache[pageIndex] = offset
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


###*
# Anchor a set of selectors.
#
# This function converts a set of selectors into a document range using.
# It encapsulates the core anchoring algorithm, using the selectors alone or
# in combination to establish the best anchor within the document.
#
# :param Array selectors: The selectors to try.
# :return: A Promise that resolves to a Range on success.
# :rtype: Promise
####
exports.anchor = (selectors, options = {}) ->
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

  anchorByPosition = (page, anchor) ->
    renderingState = page.renderingState
    renderingDone = page.textLayer?.renderingDone
    if renderingState is RenderingStates.FINISHED and renderingDone
      root = page.textLayer.textLayerDiv
      selector = anchor.toSelector()
      return html.anchor([selector], {root})
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

  if position?
    promise = promise.catch ->
      return findPage(position.start)
      .then ({index, offset, textContent}) ->
        page = getPage(index)
        start = position.start - offset
        end = position.end - offset
        length = end - start
        assertQuote(textContent.substr(start, length))
        anchor = new TextPositionAnchor(start, end)
        return anchorByPosition(page, anchor)

  if quote?
    promise = promise.catch ->
      {pagesCount} = PDFViewerApplication.pdfViewer

      pageSearches = for pageIndex in [0...pagesCount]
        page = getPage(pageIndex)
        content = getPageTextContent(pageIndex)
        offset = getPageOffset(pageIndex)
        Promise.all([content, offset, page]).then (results) ->
          [content, offset, page] = results
          pageOptions = {root: {textContent: content}}
          if position?
            # XXX: must be on one page
            start = position.start - offset
            end = position.end - offset
            pageOptions.position = {start, end}
          anchor = new TextQuoteAnchor.fromSelector(quote, pageOptions)
          return Promise.resolve(anchor)
          .then((a) -> return a.toPositionAnchor(pageOptions))
          .then((a) -> return anchorByPosition(page, a))

      pageSearches = (p.catch(-> null) for p in pageSearches)
      return Promise.all(pageSearches).then (results) ->
        for result in results when result?
          return result
        throw new Error('quote not found')

  return promise


exports.describe = (range, options = {}) ->
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

    position = new TextPositionAnchor(start, end).toSelector()

    r = document.createRange()
    r.setStartBefore(startRange.start)
    r.setEndAfter(endRange.end)

    pageOptions = {root: startTextLayer}
    quote = Promise.resolve(TextQuoteAnchor.fromRange(r, pageOptions))
    .then((a) -> a.toSelector())

    return Promise.all([position, quote])
