angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$scope', 'annotationUI', 'crossframe', 'annotationMapper',
    'streamer', 'store', 'threading'
  ]
  constructor:   (
     $scope,   annotationUI, crossframe, annotationMapper,
     streamer,   store,   threading
  ) ->
    $scope.isStream = true
    $scope.sort = name: 'Location'
    $scope.threadRoot = threading.root

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

    loadAnnotations = (frames) ->
      for f in frames
        if f.uri in loaded
          continue
        loaded.push(f.uri)
        _loadAnnotationsFrom({uri: f.uri}, 0)

    $scope.$watchCollection (-> crossframe.frames), loadAnnotations

    $scope.focus = (annotation) ->
      if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      crossframe.call('focusAnnotations', highlights)

    $scope.scrollTo = (annotation) ->
      if angular.isObject annotation
        crossframe.call('scrollToAnnotation', annotation.$$tag)

    $scope.shouldShowThread = (container) ->
      if annotationUI.hasSelectedAnnotations() and not container.parent.parent
        annotationUI.isAnnotationSelected(container.message?.id)
      else
        true

    $scope.hasFocus = (annotation) ->
      !!($scope.focusedAnnotations ? {})[annotation?.$$tag]

    $scope.notOrphan = (container) -> !container?.message?.$orphan
