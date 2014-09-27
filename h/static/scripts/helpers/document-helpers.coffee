createDocumentHelpers = [
  '$document'
  ($document) ->
    baseURI: do ->
      baseURI = $document.prop('baseURI')

      # XXX: IE workaround for the lack of document.baseURI property
      unless baseURI
        baseURI = $document.find('base').prop('href') or $document.prop('URL')

      # Strip an empty hash and end in exactly one slash
      baseURI.replace(/#$/, '').replace(/\/+$/, '/')

    absoluteURI: (path) ->
      "#{@baseURI}#{path.replace(/^\//, '')}"
]


angular.module('h.helpers')
.factory('documentHelpers', createDocumentHelpers)
