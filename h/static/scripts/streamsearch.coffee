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

    streamer.send({filter: streamfilter.getFilter()})

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
