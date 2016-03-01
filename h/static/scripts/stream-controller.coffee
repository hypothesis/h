angular = require('angular')
mail = require('./vendor/jwz')


module.exports = class StreamController
  this.$inject = [
    '$scope', '$route', '$rootScope', '$routeParams',
    'annotationUI',
    'queryParser', 'rootThread', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'annotationMapper'
  ]
  constructor: (
     $scope,   $route,   $rootScope,   $routeParams
     annotationUI,
     queryParser,   rootThread,   searchFilter,   store,
     streamer,   streamFilter,   annotationMapper
  ) ->
    offset = 0

    fetch = (limit) ->
      options = {offset, limit}
      searchParams = searchFilter.toObject($routeParams.q)
      query = angular.extend(options, searchParams)
      query._separate_replies = true
      store.SearchResource.get(query, load)

    load = ({rows, replies}) ->
        offset += rows.length
        annotationMapper.loadAnnotations(rows, replies)

    # Reload on query change (ignore hash change)
    lastQuery = $routeParams.q
    $scope.$on '$routeUpdate', ->
      if $routeParams.q isnt lastQuery
        annotationUI.clearAnnotations()
        $route.reload()

    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    terms = searchFilter.generateFacetedFilter $routeParams.q
    queryParser.populateFilter streamFilter, terms
    streamer.setConfig('filter', {filter: streamFilter.getFilter()})

    # Perform the initial search
    fetch(20)

    $scope.$watch('sort.name', (name) ->
      rootThread.sortBy(name)
    )

    $scope.toggleCollapsed = (id) ->
      annotationUI.setCollapsed(id, annotationUI.expanded[id])

    $scope.forceVisible = (id) ->
      annotationUI.setForceVisible(id, true)

    $scope.isStream = true
    $scope.sortOptions = ['Newest', 'Oldest']
    $scope.sort.name = 'Newest'
    $scope.rootThread = ->
      return rootThread.thread()
    $scope.loadMore = fetch
