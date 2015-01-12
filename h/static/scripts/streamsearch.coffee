class StreamSearchController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'annotator', 'queryparser', 'searchfilter', 'streamer', 'streamfilter'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     annotator,   queryparser,   searchfilter,   streamer,   streamfilter
  ) ->
    # Clear out loaded annotations and threads
    # XXX: Resolve threading, storage, and streamer better for all routes.
    annotator.plugins.Threading?.pluginInit()
    unless annotator.plugins.Store?
      annotator.addPlugin 'Store', annotator.options.Store
    else
      annotator.plugins.Store.annotations = []

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchfilter.toObject $scope.search.query
    annotator.plugins.Store.loadAnnotationsFromSearch terms

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
