angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$scope', 'annotationUI', 'crossframe', 'annotationMapper',
    'streamer', 'streamFilter', 'store'
  ]
  constructor:   (
     $scope,   annotationUI, crossframe, annotationMapper,
     streamer,   streamFilter,   store
  ) ->
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

    loadAnnotations = (frames) ->
      for f in frames
        if f.uri in loaded
          continue
        loaded.push(f.uri)
        _loadAnnotationsFrom({uri: f.uri}, 0)

      streamFilter.resetFilter().addClause('/uri', 'one_of', loaded)
      streamer.send({filter: streamFilter.getFilter()})

    $scope.$watchCollection (-> crossframe.frames), loadAnnotations

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
