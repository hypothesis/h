Promise = require('es6-promise').Promise
Annotator = require('annotator')


class PDF extends Annotator.Plugin
  documentLoaded: null
  observer: null
  pdfViewer: null
  updatePromise: null
  updateTimeout: null

  pluginInit: ->
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

    @observer = new MutationObserver((mutations) => this.update())
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

  update: ->
    self = this
    {annotator, pdfViewer} = this

    _throttle = ->
      if self.updateTimeout?
        clearTimeout(self.updateTimeout)
      self.updateTimeout = setTimeout(_update, 200)

    _update = ->
      anchors = []
      annotations = []

      for page in pdfViewer.pages when page.textLayer?.renderingDone
        div = page.div ? page.el
        placeholder = div.getElementsByClassName('annotator-placeholder')[0]

        switch page.renderingState
          when RenderingStates.INITIAL
            page.textLayer = null
          when RenderingStates.FINISHED
            if placeholder?
              placeholder.parentNode.removeChild(placeholder)

      for anchor in annotator.anchors when anchor.annotation not in annotations
        unless anchor.range? and anchor.highlights?
          delete anchor.range
          annotations.push(anchor.annotation)
          continue

        for hl in anchor.highlights
          if not document.body.contains(hl)
            delete anchor.range
            annotations.push(anchor.annotation)
            break

      for annotation in annotations
        annotator.setupAnnotation(annotation)
        anchors.push(annotation.anchors)

      self.updateTimeout = null
      self.updatePromise = Promise.all(anchors)

    @annotator.plugins.BucketBar?.update()
    Promise.resolve(@updatePromise).then(_throttle)

Annotator.Plugin.PDF = PDF

module.exports = PDF
