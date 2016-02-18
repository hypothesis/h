angular = require('angular')

events = require('./events')

module.exports = class WidgetController
  this.$inject = [
    '$scope', '$rootScope', 'annotationUI', 'crossframe', 'annotationMapper',
    'drafts', 'groups', 'streamer', 'streamFilter', 'store', 'threading'
  ]
  constructor:   (
     $scope,   $rootScope,   annotationUI,   crossframe,   annotationMapper,
     drafts,    groups,  streamer,   streamFilter,   store,   threading
  ) ->
    $scope.threadRoot = threading.root
    $scope.sortOptions = ['Newest', 'Oldest', 'Location']

    @chunkSize = 200
    loaded = []

    _resetAnnotations = ->
      # Unload all the annotations
      annotationMapper.unloadAnnotations(threading.annotationList())
      # Reload all the drafts
      threading.thread(drafts.unsaved())

    _loadAnnotationsFrom = (query, offset) =>
      queryCore =
        limit: @chunkSize
        offset: offset
        sort: 'created'
        order: 'asc'
        group: groups.focused().id
      q = angular.extend(queryCore, query)
      q._separate_replies = true

      store.SearchResource.get q, (results) ->
        total = results.total
        offset += results.rows.length
        if offset < total
          _loadAnnotationsFrom query, offset

        annotationMapper.loadAnnotations(results.rows, results.replies)

    loadAnnotations = (frames) ->
      for f in frames
        if f.uri in loaded
          continue
        loaded.push(f.uri)
        _loadAnnotationsFrom({uri: f.uri}, 0)

      if loaded.length > 0
        streamFilter.resetFilter().addClause('/uri', 'one_of', loaded)
        streamer.setConfig('filter', {filter: streamFilter.getFilter()})

    $scope.$on events.GROUP_FOCUSED, ->
      _resetAnnotations(annotationMapper, drafts, threading)
      loaded = []
      loadAnnotations crossframe.frames

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

    $rootScope.$on('beforeAnnotationCreated', (event, data) ->
      if data.$highlight || (data.references && data.references.length > 0)
        return
      $scope.clearSelection()
    )
