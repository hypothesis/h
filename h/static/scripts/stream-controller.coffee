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
    offset = 0

    fetch = (limit) ->
      options = {offset, limit}
      searchParams = searchFilter.toObject($routeParams.q)
      query = angular.extend(options, searchParams)
      store.SearchResource.get(query, load)

    load = ({rows}) ->
        offset += rows.length
        annotationMapper.loadAnnotations(rows)

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

    # Perform the initial search
    fetch(20)

    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.loadMore = fetch
