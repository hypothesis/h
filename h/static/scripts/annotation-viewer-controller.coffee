angular = require('angular')


module.exports = class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'streamer', 'store', 'streamFilter', 'annotationMapper', 'threading'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     streamer,   store,   streamFilter,   annotationMapper,   threading
  ) ->
    id = $routeParams.id

    # Set up the viewer
    $scope.isStream = false

    # Provide no-ops until these methods are moved elsewere. They only apply
    # to annotations loaded into the stream.
    $scope.focus = angular.noop

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    store.SearchResource.get _id: id, ({rows, replies}) ->
      annotationMapper.loadAnnotations(rows, replies)
      $scope.threadRoot = {children: [threading.idTable[id]]}

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.setConfig('filter', {filter: streamFilter.getFilter()})
