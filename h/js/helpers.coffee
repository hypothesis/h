baseURI = [
  '$document'
  ($document) ->
    # Strip an empty hash and end in exactly one slash
    $document[0].baseURI.replace(/#$/, '').replace(/\/*$/, '/')
]


angular.module('h.helpers', [])
  .factory('baseURI', baseURI)
