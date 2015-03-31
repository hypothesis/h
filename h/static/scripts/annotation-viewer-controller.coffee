angular = require('angular')


module.exports = class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'streamer', 'store', 'streamFilter', 'threading', 'annotationMapper'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     streamer,   store,   streamFilter,   threading,   annotationMapper
  ) ->
    # Tells the view that these annotations are standalone
    $scope.isEmbedded = false
    $scope.isStream = false

    $scope.threadRoot = threading?.root

    $scope.lookup.hasAnnotation = (annotation) ->
      threading.idTable[annotation.id]?.message

    $scope.lookup.getAnnotationContainers = ->
      containers = []
      for id, container of threading.idTable when container.message
        containers.push container
      containers

    # Provide no-ops until these methods are moved elsewere. They only apply
    # to annotations loaded into the stream.
    $scope.focus = angular.noop

    $scope.shouldShowThread = -> true

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    id = $routeParams.id
    store.SearchResource.get _id: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)
      $scope.threadRoot = children: [threading.getContainer(id)]
    store.SearchResource.get references: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.send({filter: streamFilter.getFilter()})
