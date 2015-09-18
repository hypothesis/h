angular = require('angular')


module.exports = class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'streamer', 'store', 'annotationMapper', 'threading'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     streamer,   store,   annotationMapper,   threading
  ) ->
    id = $routeParams.id

    # Set up the viewer
    $scope.isStream = false
    $scope.focus = angular.noop
    $scope.shouldShowThread = -> true

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    store.AnnotationResource.read id: id, (annotation) ->
      annotationMapper.loadAnnotations([annotation])
      $scope.threadRoot = {children: threading.idTable[id]}
    store.SearchResource.get references: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)
