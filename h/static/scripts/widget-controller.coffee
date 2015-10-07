angular = require('angular')


module.exports = class WidgetController
  this.$inject = [
    '$scope', 'annotationUI', 'crossframe', 'annotationMapper', 'groups',
    'streamer', 'streamFilter', 'store', 'threading'
  ]
  constructor:   (
     $scope,   annotationUI,   crossframe,   annotationMapper,   groups,
     streamer,   streamFilter,   store,   threading
  ) ->
    $scope.isStream = true
    $scope.threadRoot = threading.root

    @chunkSize = 200
    loaded = []

    _loadAnnotationsFrom = (query, offset) =>
      groups.ready().then( ->
        queryCore =
          limit: @chunkSize
          offset: offset
          sort: 'created'
          order: 'asc'
          group: groups.focused().id
        q = angular.extend(queryCore, query)

        store.SearchResource.get q, (results) ->
          total = results.total
          offset += results.rows.length
          if offset < total
            _loadAnnotationsFrom query, offset

          annotationMapper.loadAnnotations(results.rows)
      ).catch((e) ->
        throw e
      )

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

    $scope.hasFocus = (annotation) ->
      !!($scope.focusedAnnotations ? {})[annotation?.$$tag]
