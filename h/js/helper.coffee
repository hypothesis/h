baseURL = ($document) ->
  baseUrl = $document[0].baseURI

  # Strip an empty hash and end in exactly one slash
  baseUrl = baseUrl.replace /#$/, ''
  baseUrl = baseUrl.replace /\/*$/, '/'

  baseUrl

angular.module('h.helper', [])
  .factory('baseurl', ['$document', baseURL])