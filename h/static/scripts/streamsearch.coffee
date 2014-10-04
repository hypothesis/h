class StreamSearchController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'annotator', 'queryparser', 'searchfilter', 'streamfilter'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     annotator,   queryparser,   searchfilter,   streamfilter
  ) ->
    # Clear out loaded annotations and threads
    # XXX: Resolve threading, storage, and updater better for all routes.
    annotator.plugins.Threading?.pluginInit()
    annotator.plugins.Store?.annotations = []

    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()
      .setPastDataHits(50)

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchfilter.generateFacetedFilter $scope.search.query
    queryparser.populateFilter streamfilter, terms

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$watch 'updater', (updater) ->
      updater?.then (sock) ->
        filter = streamfilter.getFilter()
        sock.send(JSON.stringify({filter}))

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
