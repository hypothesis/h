detectedPDFjsVersion = PDFJS?.version.split(".").map parseFloat

# Compare two versions, given as arrays of numbers
compareVersions = (v1, v2) ->
  unless Array.isArray(v1) and Array.isArray(v2)
    throw new Error "Expecting arrays, in the form of [1, 0, 123]"
  unless v1.length is v2.length
    throw new Error "Can't compare versions in different formats."
  for i in [0 ... v1.length]
    if v1[i] < v2[i]
      return -1
    else if v1[i] > v2[i]
      return 1
  # Finished comparing, it's the same all along
  return 0

# Document mapper module for PDF.js documents
class window.PDFTextMapper extends PageTextMapperCore

  # Are we working with a PDF document?
  @isPDFDocument: ->
    PDFView? or             # for PDF.js up to v1.0.712
      PDFViewerApplication? # for PDF.js v1.0.907 and up

  # Can we use this document access strategy?
  @applicable: -> @isPDFDocument()

  requiresSmartStringPadding: true

  # Get the number of pages
  getPageCount: -> @_viewer.pages.length

  # Where are we in the document?
  getPageIndex: -> @_app.page - 1

  # Jump to a given page
  setPageIndex: (index) -> @_app.page = index + 1

  # Determine whether a given page has been rendered
  _isPageRendered: (index) ->
    @_viewer.pages[index]?.textLayer?.renderingDone

  # Get the root DOM node of a given page
  getRootNodeForPage: (index) ->
    @_viewer.pages[index].textLayer.textLayerDiv

  constructor: ->
    # Set references to objects that moved around in different versions
    # of PDF.js, and define a few methods accordingly
    if PDFViewerApplication?
      @_app = PDFViewerApplication
      @_viewer = @_app.pdfViewer
    else
      @_app = @_viewer = PDFView

    @setEvents()

    # Starting with PDF.js v1.0.822, the CSS rules changed.
    #
    # See this commit:
    # https://github.com/mozilla/pdf.js/commit/a2e8a5ee7fecdbb2f42eeeb2343faa38cd553a15
    # We need to know about that, and set our own CSS rules accordingly,
    # so that our highlights are still visible. So we add a marker class,
    # if this is the case.
    if compareVersions(detectedPDFjsVersion, [1, 0, 822]) >= 0
      @_viewer.container.className += " has-transparent-text-layer"

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
      node = event.srcElement ? event.target
      data = event.data
      if "viewer" is node.getAttribute? "id"
        console.log "Detected cross-page change event."
        # This event escaped the pages.
        # Must be a cross-page selection.
        if data.start? and data.end?
          startPage = @getPageForNode data.start
          @_updateMap @pageInfo[startPage.index]
          endPage = @getPageForNode data.end
          @_updateMap @pageInfo[endPage.index]

    @_viewer.container.addEventListener "scroll", @_onScroll

  _extractionPattern: /[ ]+/g
  _parseExtractedText: (text) => text.replace @_extractionPattern, " "

  # Wait for PDF.js to initialize
  waitForInit: ->
    # Create a utility function to poll status
    tryIt = (resolve) =>
      # Are we ready yet?
      if @_app.documentFingerprint and @_app.documentInfo
        # Now we have PDF metadata."
        resolve()
      else
        # PDF metadata is not yet available; postponing extraction.
        setTimeout ( =>
          # let's try again if we have PDF metadata.
          tryIt resolve
        ), 100

    # Return a promise
    new Promise (resolve, reject) =>
      if PDFTextMapper.applicable()
        tryIt resolve
      else
        reject "Not a PDF.js document"

  # Extract the text from the PDF
  scan: ->
    # Return a promise
    new Promise (resolve, reject) =>
      @_pendingScanResolve = resolve
      @waitForInit().then =>

        # Initialize our main page data array
        @pageInfo = []

        # Start the text extraction
        @_extractPageText 0

  # Manually extract the text from the PDF document.
  # This workaround is here to avoid depending PDFFindController's
  # own text extraction routines, which sometimes fail to add
  # adequate spacing.
  _extractPageText: (pageIndex) ->
    # Wait for the page to load
    @_app.pdfDocument.getPage(pageIndex + 1).then (page) =>

      # Wait for the data to be extracted
      page.getTextContent().then (data) =>

        # There is some variation about what I might find here,
        # depending on PDF.js version, so we need to do some guesswork.
        textData = data.bidiTexts ? data.items ? data

        # First, join all the pieces from the bidiTexts
        rawContent = (text.str for text in textData).join " "

        # Do some post-processing
        content = @_parseExtractedText rawContent

        # Save the extracted content to our page information registery
        @pageInfo[pageIndex] =
          index: pageIndex
          content: content

        if pageIndex is @getPageCount() - 1
          @_finishScan()
        else
          @_extractPageText pageIndex + 1

  # This is called when scanning is finished
  _finishScan: =>
    # Do some besic calculations with the content
    @_onHavePageContents()

    # OK, we are ready to rock.
    @_pendingScanResolve()

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

  getDocumentFingerprint: -> @_app.documentFingerprint
  getDocumentInfo: -> @_app.documentInfo

# Annotator plugin for annotating documents handled by PDF.js
class Annotator.Plugin.PDF extends Annotator.Plugin

  $ = Annotator.$

  pluginInit: ->
    # We need dom-text-mapper
    unless @annotator.plugins.DomTextMapper
      console.warn "The PDF Annotator plugin requires the DomTextMapper plugin. Skipping."
      return

    @anchoring = @annotator.anchoring

    @anchoring.documentAccessStrategies.unshift
      # Strategy to handle PDF documents rendered by PDF.js
      name: "PDF.js"
      mapper: PDFTextMapper

  # Are we looking at a PDF.js-rendered document?
  _isPDF: -> PDFTextMapper.applicable()

  # Extract the URL of the PDF file, maybe from the chrome-extension URL
  _getDocumentURI: ->
    uri = window.location.href

    # We might have the URI embedded in a chrome-extension URI
    matches = uri.match('chrome-extension://[a-z]{32}/(content/web/viewer.html\\?file=)?(.*)')

    # Get the last match
    match = matches?[matches.length - 1]

    if match
      decodeURIComponent match
    else
      uri

  # Get a PDF fingerPrint-based URI
  _getFingerPrintURI: ->
    fingerprint = @anchoring.document.getDocumentFingerprint()

    # This is an experimental URN,
    # as per http://tools.ietf.org/html/rfc3406#section-3.0
    "urn:x-pdf:" + fingerprint

  # Public: get a canonical URI, if this is a PDF. (Null otherwise)
  uri: ->
    return null unless @_isPDF()

    # For now, we return the fingerprint-based URI first,
    # because it's probably more relevant.
    # OTOH, we can't use it for clickable source links ...
    # but the path is also included in the matadata,
    # so anybody who _needs_ that can access it from there.
    @_getFingerPrintURI()

  # Try to extract the title; first from metadata, then HTML header
  _getTitle: ->
    title = @anchoring.document.getDocumentInfo().Title?.trim()
    if title? and title isnt ""
      title
    else
      $("head title").text().trim()

  # Get metadata
  _metadata: ->
    metadata =
      link: [{
        href: @_getFingerPrintURI()
      }]
      title: @_getTitle()

    documentURI = @_getDocumentURI()
    if documentURI.toLowerCase().indexOf('file://') is 0
        metadata.filename = new URL(documentURI).pathname.split('/').pop()
    else
        metadata.link.push {href: documentURI}

    metadata

  # Public: Get metadata (when the doc is loaded). Returns a promise.
  getMetaData: =>
    new Promise (resolve, reject) =>
      if @anchoring.document.waitForInit?
        @anchoring.document.waitForInit().then =>
          try
            resolve @_metadata()
          catch error
            reject "Internal error"
      else
        reject "Not a PDF dom mapper."

  # We want to react to some events
  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'

  # This is what we do to new annotations
  beforeAnnotationCreated: (annotation) =>
    return unless @_isPDF()
    annotation.document = @_metadata()
