angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$scope', 'annotationUI', 'crossframe', 'annotationMapper',
    'streamer', 'streamFilter', 'store', 'threading'
  ]
  constructor:   (
     $scope,   annotationUI, crossframe, annotationMapper,
     streamer,   streamFilter,   store,   threading
  ) ->
    $scope.isStream = true
    $scope.isSidebar = true
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

      if loaded.length > 0
        streamFilter.resetFilter().addClause('/uri', 'one_of', loaded)
        streamer.send({filter: streamFilter.getFilter()})

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
      # Show stubs
      if not container?.message?
        return true

      # Show replies
      if container.message.references?.length
        return true

      # Show selected threads
      if annotationUI.hasSelectedAnnotations()
        return annotationUI.isAnnotationSelected(container.message.id)

      # Show regardless of $anchored if that feature is turned on
      if $scope.feature('show_unanchored_annotations')
        return true

      # Show anchored threads
      if container.message.$anchored
        return true

      return false

    $scope.hasFocus = (annotation) ->
      !!($scope.focusedAnnotations ? {})[annotation?.$$tag]
