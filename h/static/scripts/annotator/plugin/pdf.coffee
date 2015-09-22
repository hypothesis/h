extend = require('extend')
Annotator = require('annotator')


module.exports = class PDF extends Annotator.Plugin
  documentLoaded: null
  observer: null
  pdfViewer: null

  pluginInit: ->
    @annotator.anchoring = require('../anchoring/pdf')

    @pdfViewer = PDFViewerApplication.pdfViewer
    @pdfViewer.viewer.classList.add('has-transparent-text-layer')

    if PDFViewerApplication.loading
      @documentLoaded = new Promise (resolve) ->
        finish = (evt) ->
          window.removeEventListener('documentload', finish)
          resolve()
        window.addEventListener('documentload', finish)
    else
      @documentLoaded = Promise.resolve()

    @observer = new MutationObserver((mutations) => this._update())
    @observer.observe(@pdfViewer.viewer, {
      attributes: true
      attributeFilter: ['data-loaded']
      childList: true
      subtree: true
    })

  destroy: ->
    @pdfViewer.viewer.classList.remove('has-transparent-text-layer')
    @observer.disconnect()

  uri: ->
    @documentLoaded.then ->
      PDFViewerApplication.url

  getMetadata: ->
    @documentLoaded.then ->
      info = PDFViewerApplication.documentInfo
      metadata = PDFViewerApplication.metadata

      # Taken from PDFViewerApplication#load
      if metadata?.has('dc:title') and metadata.get('dc:title') isnt 'Untitled'
        title = metadata.get('dc:title')
      else if info?['Title']
        title = info['Title']
      else
        title = document.title

      # This is an experimental URN,
      # as per http://tools.ietf.org/html/rfc3406#section-3.0
      urn = "urn:x-pdf:" + PDFViewerApplication.documentFingerprint
      link = [{href: urn}, {href: PDFViewerApplication.url}]

      return {title, link}

  # This method (re-)anchors annotations when pages are rendered and destroyed.
  _update: ->
    {annotator, pdfViewer} = this

    # A list of annotations that need to be refreshed.
    refreshAnnotations = []

    # Check all the pages with text layers that have finished rendering.
    for pageIndex in [0...pdfViewer.pagesCount]
      page = pdfViewer.getPageView(pageIndex)
      continue unless page.textLayer?.renderingDone

      div = page.div ? page.el
      placeholder = div.getElementsByClassName('annotator-placeholder')[0]

      # Detect what needs to be done by checking the rendering state.
      switch page.renderingState
        when RenderingStates.INITIAL
          # This page has been reset to its initial state so its text layer
          # is no longer valid. Null it out so that we don't process it again.
          page.textLayer = null
        when RenderingStates.FINISHED
          # This page is still rendered. If it has a placeholder node that
          # means the PDF anchoring module anchored annotations before it was
          # rendered. Remove this, which will cause the annotations to anchor
          # again, below.
          if placeholder?
            placeholder.parentNode.removeChild(placeholder)

    # Find all the anchors that have been invalidated by page state changes.
    for anchor in annotator.anchors when anchor.highlights?
      # Skip any we already know about.
      if anchor.annotation in refreshAnnotations
        continue

      # If the highlights are no longer in the document it means that either
      # the page was destroyed by PDF.js or the placeholder was removed above.
      # The annotations for these anchors need to be refreshed.
      for hl in anchor.highlights
        if not document.body.contains(hl)
          delete anchor.highlights
          delete anchor.range
          refreshAnnotations.push(anchor.annotation)
          break

    for annotation in refreshAnnotations
      annotator.anchor(annotation)
