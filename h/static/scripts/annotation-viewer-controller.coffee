angular = require('angular')


module.exports = class AnnotationViewerController
  this.$inject = [
    '$location', '$rootScope', '$routeParams', '$scope',
    'annotationMapper', 'drafts', 'streamer', 'store', 'streamFilter',
    'threading'
  ]
  constructor: (
     $location,   $rootScope,   $routeParams,   $scope,
     annotationMapper,   drafts,   streamer,   store,   streamFilter,
     threading
  ) ->
    $scope.threading = threading
    $scope.threadRoot = $scope.threading?.root

    # Tells the view that these annotations are standalone
    $scope.isEmbedded = false
    $scope.isStream = false

    # Provide no-ops until these methods are moved elsewhere. They only apply
    # to annotations loaded into the stream.
    $scope.focus = angular.noop

    $scope.shouldShowThread = -> true

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    id = $routeParams.id
    store.SearchResource.get _id: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)
      $scope.threadRoot = children: [$scope.threading.getContainer(id)]
    store.SearchResource.get references: id, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.send({filter: streamFilter.getFilter()})

    # Listen to updates
    streamer.onmessage = (data) ->
      return if !data or data.type != 'annotation-notification'
      action = data.options.action
      payload = data.payload

      return unless payload.length
      switch action
        when 'create', 'update', 'past'
          annotationMapper.loadAnnotations payload
        when 'delete'
          for annotation in payload
            if a = threading.idTable[annotation.id]?.message
              $scope.$emit('annotationDeleted', a)

      $scope.$digest()

    listener = $rootScope.$on 'cleanupAnnotations', (event) ->
      # Clean up any annotations
      for id, container of $scope.threading.idTable when container.message
        $scope.$emit('annotationDeleted', container.message)
        drafts.remove container.message

    $scope.$on '$destroy', ->
      listener()
