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

  onpagerendered: =>
    succeed = ({annotation, target}) ->
      (highlights) -> {annotation, target, highlights}

    fail = ({annotation, target}) ->
      (reason) -> {annotation, target}

    finish = (results) =>
      anchored = @annotator.anchored
      unanchored = @annotator.unanchored
      updated = for result in results when result.highlights?
        delete result.annotation.$orphan
        anchored.push(result)
        result
      @annotator.unanchored = unanchored.filter((o) -> o not in anchored)
      @annotator.plugins.CrossFrame.sync(updated) if updated.length

    promises = for obj in @annotator.unanchored
      @annotator.anchorTarget(obj.target).then(succeed(obj), fail(obj))

    Promise.all(promises).then(finish)

Annotator.Plugin.PDF = PDF

module.exports = PDF
