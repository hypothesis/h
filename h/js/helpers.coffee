baseURI = [
  '$document'
  ($document) ->
    # Strip an empty hash and end in exactly one slash
    baseURI = $document[0].baseURI
    # XXX: IE workaround for the lack of document.baseURI property
    if not baseURI
      baseTags = $document[0].getElementsByTagName "base"
      baseURI = if baseTags.length then baseTags[0].href else $document[0].URL
    baseURI.replace(/#$/, '').replace(/\/+$/, '/')
]


angular.module('h.helpers', [])
  .factory('baseURI', baseURI)
