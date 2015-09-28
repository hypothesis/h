angular = require('angular')


module.exports = class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'streamer', 'store', 'streamFilter', 'annotationMapper'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     streamer,   store,   streamFilter,   annotationMapper
  ) ->
    id = $routeParams.id

    # Set up the viewer
    $scope.isStream = false

    # Provide no-ops until these methods are moved elsewere. They only apply
    # to annotations loaded into the stream.
    $scope.focus = angular.noop

    $scope.shouldShowThread = -> true

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    store.AnnotationResource.read id: id, (annotation) ->
      annotationMapper.loadAnnotations([annotation])
      $scope.threads = -> [annotationMapper.thread(id)]
    store.SearchResource.get references: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.send({filter: streamFilter.getFilter()})
