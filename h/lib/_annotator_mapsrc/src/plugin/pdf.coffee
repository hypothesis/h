# Document mapper module for PDF.js documents
class window.PDFTextMapper extends window.PageTextMapperCore

  # Are we working with a PDF document?
  @applicable: -> PDFView?.initialized ? false

  requiresSmartStringPadding: true

  # Get the number of pages
  getPageCount: -> PDFView.pages.length

  # Where are we in the document?
  getPageIndex: -> PDFView.page - 1

  # Jump to a given page
  setPageIndex: (index) -> PDFView.page = index + 1

  # Determine whether a given page has been rendered
  _isPageRendered: (index) ->
    return PDFView.pages[index]?.textLayer?.renderingDone

  # Get the root DOM node of a given page
  getRootNodeForPage: (index) ->
    PDFView.pages[index].textLayer.textLayerDiv

  constructor: ->
    @setEvents()

  # Install watchers for various events to detect page rendering/unrendering
  setEvents: ->
    # Detect page rendering
    addEventListener "pagerender", (evt) =>

      # If we have not yet finished the initial scanning, then we are
      # not interested.
      return unless @pageInfo?

      index = evt.detail.pageNumber - 1
      @_onPageRendered index

    # Detect page un-rendering
    addEventListener "DOMNodeRemoved", (evt) =>
      node = evt.target
      if node.nodeType is Node.ELEMENT_NODE and node.nodeName.toLowerCase() is "div" and node.className is "textLayer"
        index = parseInt node.parentNode.id.substr(13) - 1

        # Forget info about the new DOM subtree
        @_unmapPage @pageInfo[index]

    # Do something about cross-page selections
    viewer = document.getElementById "viewer"
    viewer.addEventListener "domChange", (event) =>
      node = event.srcElement
      data = event.data
      if "viewer" is node.getAttribute? "id"
        console.log "Detected cross-page change event."
        # This event escaped the pages.
        # Must be a cross-page selection.
        if data.start? and data.end?
          startPage = @getPageForNode data.start
          endPage = @getPageForNode data.end
          for index in [ startPage.index .. endPage.index ]
            #console.log "Should rescan page #" + index
            @_updateMap @pageInfo[index]

    $(PDFView.container).on 'scroll', => @_onScroll()

  _extractionPattern: /[ ]+/g
  _parseExtractedText: (text) => text.replace @_extractionPattern, " "

  # Extract the text from the PDF
  scan: ->
    # Create a promise, unless we already have one
    @pendingScan ?= new PDFJS.Promise()

    # Do we have a document yet?
    unless PDFView.pdfDocument?
      # If not, then wait for half a second, and retry
      #console.log "Delaying scan, because there is no document yet."
      setTimeout (=> @scan()), 500
      return @pendingScan

    # Wait for the document to load
    PDFView.getPage(1).then =>
      console.log "Scanning document for text..."

      @pageInfo = []
      @_extractPageText 0

    # Return the promise
    @pendingScan

  # Manually extract the text from the PDF document.
  # This workaround is here to avoid depending PDFFindController's
  # own text extraction routines, which sometimes fail to add
  # adequate spacing.
  _extractPageText: (pageIndex) ->
    # Get a handle on the page
    page = PDFFindController.pdfPageSource.pages[pageIndex]

    # Start the collection of page contents
    page.getTextContent().then (data) =>

      # First, join all the pieces from the bidiTexts
      rawContent = (text.str for text in data.bidiTexts).join " "

      # Do some post-processing
      content = @_parseExtractedText rawContent

      # Save the extracted content to our page information registery
      @pageInfo[pageIndex] = content: content

      if pageIndex is PDFView.pages.length - 1
        @_finishScan()
      else
        @_extractPageText pageIndex + 1

  # This is called when scanning is finished
  _finishScan: =>
    # Do some besic calculations with the content
    @_onHavePageContents()

    # OK, we are ready to rock.
    @pendingScan.resolve()

    # Do whatever we need to do after scanning
    @_onAfterScan()


  # Look up the page for a given DOM node
  getPageForNode: (node) ->
    # Search for the root of this page
    div = node
    while (
      (div.nodeType isnt Node.ELEMENT_NODE) or
      not div.getAttribute("class")? or
      (div.getAttribute("class") isnt "textLayer")
    )
      div = div.parentNode

    # Fetch the page number from the id. ("pageContainerN")
    index = parseInt div.parentNode.id.substr(13) - 1

    # Look up the page
    @pageInfo[index]


# Annotator plugin for annotating documents handled by PDF.js
class Annotator.Plugin.PDF extends Annotator.Plugin

  pluginInit: ->
    # We need dom-text-mapper
    unless @annotator.plugins.DomTextMapper
      throw "The PDF Annotator plugin requires the DomTextMapper plugin."

    @annotator.documentAccessStrategies.unshift
      # Strategy to handle PDF documents rendered by PDF.js
      name: "PDF.js"
      mapper: PDFTextMapper
