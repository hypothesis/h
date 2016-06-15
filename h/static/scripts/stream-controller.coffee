angular = require('angular')

module.exports = class StreamController
  this.$inject = [
    '$scope', '$location', '$route', '$rootScope', '$routeParams',
    'annotationUI',
    'queryParser', 'rootThread', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'annotationMapper'
  ]
  constructor: (
     $scope,  $location,   $route,   $rootScope,   $routeParams
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

    $scope.setCollapsed = (id, collapsed) ->
      annotationUI.setCollapsed(id, collapsed)

    $scope.forceVisible = (id) ->
      annotationUI.setForceVisible(id, true)

    Object.assign $scope.search, {
      query: -> $routeParams.q || ''
      update: (q) -> $location.search({q: q})
    }

    thread = ->
      rootThread.thread(annotationUI.getState())

    annotationUI.subscribe( ->
      $scope.virtualThreadList = {
        visibleThreads: thread().children,
        offscreenUpperHeight: '0px',
        offscreenLowerHeight: '0px',
      };
    );

    # Sort the stream so that the newest annotations are at the top
    annotationUI.setSortKey('Newest')

    $scope.isStream = true
    $scope.loadMore = fetch
