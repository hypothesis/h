class StreamSearchController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'annotator', 'auth', 'queryparser', 'searchfilter', 'store',
    'streamer', 'streamfilter'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     annotator,   auth,   queryparser,   searchfilter,   store,
     streamer,   streamfilter
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchfilter.generateFacetedFilter $scope.search.query
    queryparser.populateFilter streamfilter, terms

    # Perform the search
    query = angular.extend limit: 10, $scope.search.query
    store.SearchResource.get query, ({rows}) ->
      annotator.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
