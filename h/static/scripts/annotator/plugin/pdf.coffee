Promise = require('es6-promise').Promise
Annotator = require('annotator')


class PDF extends Annotator.Plugin
  documentPromise: null

  pluginInit: ->
    @documentPromise = new Promise (resolveDocument, rejectDocument) ->
      resolveDocumentAndCleanup = (evt) ->
        window.removeEventListener('documentload', resolveDocumentAndCleanup)
        debugger
        resolveDocument(evt)
      window.addEventListener('documentload', resolveDocument)

    window.addEventListener('pagerendered', @onpagerendered)

  destroy: ->
    window.removeEventListener('pagerendered', @onpagerendered)

  getMetadata: ->
    Promise.resolve({})

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
