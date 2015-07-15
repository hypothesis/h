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
  return PDFViewerApplication.pdfViewer.pages[pageIndex]


getPageTextContent = (pageIndex) ->
  if pageTextCache[pageIndex]?
    return Promise.resolve(pageTextCache[pageIndex])
  else
    joinItems = ({items}) ->
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


###*
# Anchor a set of selectors.
#
# This function converts a set of selectors into a document range using.
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

  anchorByPosition = (page, anchor) ->
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
        return anchorByPosition(page, anchor)

  if quote?
    promise = promise.catch ->
      {pagesCount} = PDFViewerApplication.pdfViewer

      if position?
        if quotePositionCache[quote.exact]?[position.start]?
         {page, anchor} = quotePositionCache[quote.exact][position.start]
         return anchorByPosition(page, anchor)

      findInPages = ([pageIndex, rest...]) ->
        page = getPage(pageIndex)
        content = getPageTextContent(pageIndex)
        offset = getPageOffset(pageIndex)
        Promise.all([content, offset, page])
        .then (results) ->
          [content, offset, page] = results
          root = {textContent: content}
          pageOptions = {}
          if position?
            pageOptions.hint = position.start - offset
          anchor = new TextQuoteAnchor.fromSelector(root, quote)
          anchor = anchor.toPositionAnchor(pageOptions)
          quotePositionCache[quote.exact] ?= {}
          quotePositionCache[quote.exact][position.start] = {page, anchor}
          return anchorByPosition(page, anchor)
        .catch ->
          if rest.length
            return findInPages(rest)
          else
            throw new Error('quote not found')

      pages = [0...pagesCount]

      if position?
        return findPage(position.start)
        .then ({index, offset, textContent}) ->
          left = pages.slice(0, index)
          right = pages.slice(index)
          pages = []
          while left.length or right.length
            if right.length
              pages.push(right.shift())
            if left.length
              pages.push(left.pop())
          return findInPages(pages)
      else
        findInPages(pages)

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
