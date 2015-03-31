angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$scope', 'annotationUI', 'crossframe', 'annotationMapper',
    'auth', 'streamer', 'streamFilter', 'store', 'threading'
  ]
  constructor:   (
     $scope,   annotationUI, crossframe, annotationMapper,
     auth,   streamer,   streamFilter,   store,   threading
  ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    $scope.threadRoot = threading?.root

    $scope.lookup.hasAnnotation = (annotation) ->
      threading.idTable[annotation.id]?.message

    $scope.lookup.getAnnotationContainers = ->
      containers = []
      for id, container of threading.idTable when container.message
        containers.push container
      containers

    loaded = []

    _loadAnnotationsFrom = (query, offset) ->
      queryCore =
        limit: 20
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
