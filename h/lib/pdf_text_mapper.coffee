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
    window.DomTextMapper.instances.push
      id: "cross-page catcher"
      rootNode: document.getElementById "viewer"
      performUpdateOnNode: (node, data) =>
        if "viewer" is node.getAttribute? "id"
          # This event escaped the pages.
          # Must be a cross-page selection.
          if data.start? and data.end?
            startPage = @getPageForNode data.start
            endPage = @getPageForNode data.end
            for index in [ startPage.index .. endPage.index ]
              #console.log "Should rescan page #" + index
              @_updateMap @pageInfo[index]
      documentChanged: ->
      timestamp: ->

  _extractionPattern: /[ ]+/g
  _parseExtractedText: (text) => text.replace @_extractionPattern, " "

  # Extract the text from the PDF
  scan: ->
    console.log "Scanning document for text..."

    # Create a promise
    pendingScan = new PDFJS.Promise()

    # Tell the Find Controller to go digging
    PDFFindController.extractText()

    # When all the text has been extracted
    PDFJS.Promise.all(PDFFindController.extractTextPromises).then =>
      # PDF.js text extraction has finished.

      # Post-process the extracted text
      @pageInfo = ({ content: @_parseExtractedText page } for page in PDFFindController.pageContents)

      # Do some besic calculations with the content
      @_onHavePageContents()

      # OK, we are ready to rock.
      pendingScan.resolve()

      # Do whatever we need to do after scanning
      @_onAfterScan()

    # Return the promise
    pendingScan


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
