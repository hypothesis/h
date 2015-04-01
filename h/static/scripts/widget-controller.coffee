angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$rootScope', '$scope', 'annotationMapper', 'annotationUI', 'crossframe',
    'drafts', 'streamer', 'streamFilter', 'store', 'threading'
  ]
  constructor:   (
     $rootScope,   $scope,   annotationMapper,   annotationUI,   crossframe,
     drafts,   streamer,   streamFilter,   store,   threading
  ) ->
    $scope.threading = threading
    $scope.threadRoot = $scope.threading?.root

    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    @chunkSize = 200
    loaded = []

    _loadAnnotationsFrom = (query, offset) =>
      queryCore =
        limit: @chunkSize
        offset: offset
        sort: 'created'
        order: 'asc'
      q = angular.extend(queryCore, query)

      store.SearchResource.get q, (results) ->
        total = results.total
        offset += results.rows.length
        if offset < total
          _loadAnnotationsFrom query, offset

        annotationMapper.loadAnnotations(results.rows)

    loadAnnotations = ->
      query = {}

      for p in crossframe.providers
        for e in p.entities when e not in loaded
          loaded.push e
          q = angular.extend(uri: e, query)
          _loadAnnotationsFrom q, 0

      streamFilter.resetFilter().addClause('/uri', 'one_of', loaded)

      streamer.send({filter: streamFilter.getFilter()})

    $scope.$watchCollection (-> crossframe.providers), loadAnnotations

    $scope.focus = (annotation) ->
      if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      crossframe.notify
        method: 'focusAnnotations'
        params: highlights

    $scope.scrollTo = (annotation) ->
      if angular.isObject annotation
        crossframe.notify
          method: 'scrollToAnnotation'
          params: annotation.$$tag

    $scope.shouldShowThread = (container) ->
      if annotationUI.hasSelectedAnnotations() and not container.parent.parent
        annotationUI.isAnnotationSelected(container.message?.id)
      else
        true

    $scope.hasFocus = (annotation) ->
      !!($scope.focusedAnnotations ? {})[annotation?.$$tag]

    $scope.notOrphan = (container) -> !container?.message?.$orphan

    listener = $rootScope.$on 'cleanupAnnotations', ->
      # Clean up any annotations
      for id, container of $scope.threading.idTable when container.message
        $scope.$emit('annotationDeleted', container.message)
        drafts.remove container.message

    $scope.$on '$destroy', ->
      listener()

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
