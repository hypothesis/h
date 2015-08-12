angular = require('angular')
mail = require('./vendor/jwz')


module.exports = class StreamController
  this.inject = [
    '$scope', '$route', '$rootScope', '$routeParams',
    'queryParser', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'threading', 'annotationMapper'
  ]
  constructor: (
     $scope,   $route,   $rootScope,   $routeParams
     queryParser,   searchFilter,   store,
     streamer,   streamFilter,   threading,   annotationMapper
  ) ->
    # Disable the thread filter (client-side search)
    $scope.$on '$routeChangeSuccess', ->
      if $scope.threadFilter?
        $scope.threadFilter.active(false)
        $scope.threadFilter.freeze(true)

    # Reload on query change (ignore hash change)
    lastQuery = $routeParams.q
    $scope.$on '$routeUpdate', ->
      if $routeParams.q isnt lastQuery
        $route.reload()

    # XXX: Reset the threading service
    threading.createIdTable([])
    $scope.threadRoot = threading.root = mail.messageContainer()

    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    terms = searchFilter.generateFacetedFilter $routeParams.q
    queryParser.populateFilter streamFilter, terms
    streamer.send({filter: streamFilter.getFilter()})

    # Perform the search
    searchParams = searchFilter.toObject $routeParams.q
    query = angular.extend limit: 20, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.loadMore = (number) ->
      streamer.send({messageType: 'more_hits', moreHits: number})
