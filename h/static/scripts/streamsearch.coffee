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

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''

    $scope.$watch (-> auth.user), ->
      query = angular.extend limit: 10, $scope.search.query
      store.SearchResource.get query, ({rows}) ->
        annotator.loadAnnotations(rows)


angular.module('h')
.controller('StreamSearchController', StreamSearchController)
