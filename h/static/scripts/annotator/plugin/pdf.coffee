raf = require('raf')
Promise = require('es6-promise').Promise
Annotator = require('annotator')


class PDF extends Annotator.Plugin
  documentPromise: null

  pluginInit: ->
    if PDFViewerApplication.loading
      @documentLoaded = new Promise (resolve) ->
        finish = (evt) ->
          window.removeEventListener('documentload', finish)
          resolve()
        window.addEventListener('documentload', finish)
    else
      @documentLoaded = Promise.resolve()

    document.addEventListener('pagerendered', @onpagerendered)

  destroy: ->
    document.removeEventListener('pagerendered', @onpagerendered)

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

  onpagerendered: (event) =>
    annotator = @annotator
    unanchored = @annotator.unanchored
    page = PDFViewerApplication.pdfViewer.pages[event.detail.pageNumber - 1]

    waitForTextLayer = ->
      unless (page.textLayer.renderingDone)
        return new Promise(raf).then(waitForTextLayer)

    reanchor = ->
      unanchored = unanchored.splice(0, unanchored.length)
      for obj in unanchored
        annotator.setupAnnotation(obj.annotation)

    waitForTextLayer().then(reanchor)

Annotator.Plugin.PDF = PDF

module.exports = PDF
