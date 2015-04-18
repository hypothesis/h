angular = require('angular')


module.exports = class StreamController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'queryParser', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'annotationMapper'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     queryParser,   searchFilter,   store,
     streamer,   streamFilter, annotationMapper
  ) ->
    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchFilter.generateFacetedFilter $scope.search.query
    queryParser.populateFilter streamFilter, terms
    streamer.send({filter: streamFilter.getFilter()})

    # Perform the search
    searchParams = searchFilter.toObject $scope.search.query
    query = angular.extend limit: 20, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''
