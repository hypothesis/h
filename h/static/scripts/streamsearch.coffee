class StreamSearchController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'auth', 'queryparser', 'searchfilter', 'store',
    'streamer', 'streamfilter', 'annotationMapper'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     auth,   queryparser,   searchfilter,   store,
     streamer,   streamfilter, annotationMapper
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchfilter.generateFacetedFilter $scope.search.query
    queryparser.populateFilter streamfilter, terms
    streamer.send({filter: streamfilter.getFilter()})

    # Perform the search
    searchParams = searchfilter.toObject $scope.search.query
    query = angular.extend limit: 10, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
