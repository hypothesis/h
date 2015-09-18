angular = require('angular')

parseQuery = require('./parse-query')


module.exports = class StreamController
  this.inject = [
    '$scope', '$route', '$rootScope', '$routeParams',
    'store', 'streamer', 'threading', 'annotationMapper'
  ]
  constructor: (
     $scope,   $route,   $rootScope,   $routeParams
     store,   streamer,   threading,   annotationMapper
  ) ->
    offset = 0

    fetch = (limit) ->
      options = {offset, limit}
      query = parseQuery($routeParams.q)
      query = angular.extend(options, query)
      store.SearchResource.get(query, load)

    load = ({rows}) ->
        offset += rows.length
        annotationMapper.loadAnnotations(rows)

    # Reload on query change (ignore hash change)
    lastQuery = $routeParams.q
    $scope.$on '$routeUpdate', ->
      if $routeParams.q isnt lastQuery
        $route.reload()

    # Perform the initial search
    fetch(20)

    $scope.isStream = true
    $scope.sort = name: 'Newest'
    $scope.threadRoot = threading.root
    $scope.shouldShowThread = (container) -> true
    $scope.loadMore = fetch
