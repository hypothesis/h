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

    store.AnnotationResource.get id: id, (annotation) ->
      annotationMapper.loadAnnotations([annotation])
      $scope.threadRoot = {children: [threading.idTable[id]]}
    store.SearchResource.get references: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.setConfig('filter', {filter: streamFilter.getFilter()})
