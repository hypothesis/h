class StreamSearchController
  this.inject = [
    '$scope', '$location', '$rootScope', '$routeParams',
    'annotator', 'queryparser', 'searchfilter', 'streamfilter'
  ]
  constructor: (
     $scope,   $location,   $rootScope,   $routeParams
     annotator,   queryparser,   searchfilter,   streamfilter
  ) ->

    setQuery = (query) ->
      streamfilter
        .resetFilter()
        .setMatchPolicyIncludeAll()
        .setPastDataHits(50)

      # Apply query clauses
      $scope.search.query = query
      terms = searchfilter.generateFacetedFilter $scope.search.query
      queryparser.populateFilter streamfilter, terms


    # Clear out loaded annotations and threads
    # XXX: Resolve threading, storage, and updater better for all routes.
    annotator.plugins.Threading?.pluginInit()
    annotator.plugins.Store?.annotations = []

    # Initialize the base filter
    socket = null
    setQuery $routeParams.q

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$watch 'updater', (updater) ->
      updater?.then (sock) ->
        socket = sock
        filter = streamfilter.getFilter()
        sock.send(JSON.stringify({filter}))

    $scope.$on '$locationChangeSuccess', ->
      setQuery $location.search().q
      filter = streamfilter.getFilter()
      socket.send(JSON.stringify({filter}))

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
