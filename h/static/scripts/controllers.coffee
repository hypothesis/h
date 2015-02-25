# Watch the UI state and update scope properties.
class AnnotationUIController
  this.$inject = ['$rootScope', '$scope', 'annotationUI']
  constructor:   ( $rootScope,   $scope,   annotationUI ) ->
    $rootScope.$watch (-> annotationUI.selectedAnnotationMap), (map={}) ->
      count = Object.keys(map).length
      $scope.selectedAnnotationsCount = count

      if count
        $scope.selectedAnnotations = map
      else
        $scope.selectedAnnotations = null

    $rootScope.$watch (-> annotationUI.focusedAnnotationMap), (map={}) ->
      $scope.focusedAnnotations = map

    $rootScope.$on 'annotationDeleted', (event, annotation) ->
      annotationUI.removeSelectedAnnotation(annotation)


class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$route', '$scope', '$window',
    'auth', 'drafts', 'identity',
    'permissions', 'streamer', 'annotationUI',
    'annotationMapper', 'threading'
  ]
  constructor: (
     $controller,   $document,   $location,   $route,   $scope,   $window,
     auth,   drafts,   identity,
     permissions,   streamer,   annotationUI,
     annotationMapper, threading
  ) ->
    $controller(AnnotationUIController, {$scope})

    $scope.auth = auth
    isFirstRun = $location.search().hasOwnProperty('firstrun')

    streamerUrl = new URL('/ws', $document.prop('baseURI'))
    streamerUrl.protocol = streamerUrl.protocol.replace('http', 'ws')
    streamerUrl = streamerUrl.href

    applyUpdates = (action, data) ->
      # Update the application with new data from the websocket.
      return unless data?.length
      switch action
        when 'create', 'update', 'past'
          annotationMapper.loadAnnotations data
        when 'delete'
          for annotation in data
            if a = threading.idTable[annotation.id]?.message
              $scope.$emit('annotationDeleted', a)

    streamer.onmessage = (data) ->
      return if !data or data.type != 'annotation-notification'
      action = data.options.action
      payload = data.payload
      applyUpdates(action, payload)
      $scope.$digest()

    oncancel = ->
      $scope.dialog.visible = false

    cleanupAnnotations = ->
      # Clean up any annotations that need to be unloaded.
      for id, container of $scope.threading.idTable when container.message
        # Remove annotations not belonging to this user when highlighting.
        if annotationUI.tool is 'highlight' and annotation.user != auth.user
          $scope.$emit('annotationDeleted', container.message)
          drafts.remove annotation
        # Remove annotations the user is not authorized to view.
        else if not permissions.permits 'read', container.message, auth.user
          $scope.$emit('annotationDeleted', container.message)
          drafts.remove container.message

    $scope.$watch 'sort.name', (name) ->
      return unless name
      predicate = switch name
        when 'Newest' then ['-!!message', '-message.updated']
        when 'Oldest' then ['-!!message',  'message.updated']
        when 'Location' then ['-!!message', 'message.target[0].pos.top']
      $scope.sort = {name, predicate}

    $scope.$watch (-> auth.user), (newVal, oldVal) ->
      return if newVal is oldVal

      if isFirstRun and not (newVal or oldVal)
        $scope.login()
      else
        $scope.dialog.visible = false

      # Update any edits in progress.
      for draft in drafts.all()
        $scope.$emit('beforeAnnotationCreated', draft)

      # Reopen the streamer.
      streamer.close()
      streamer.open($window.WebSocket, streamerUrl)

      # Clean up annotations that should be removed
      cleanupAnnotations()

      # Reload the view.
      $route.reload()

    $scope.login = ->
      $scope.dialog.visible = true
      identity.request {oncancel}

    $scope.logout = ->
      return unless drafts.discard()
      $scope.dialog.visible = false
      identity.logout()

    $scope.loadMore = (number) ->
      streamer.send({messageType: 'more_hits', moreHits: number})

    $scope.clearSelection = ->
      $scope.search.query = ''
      annotationUI.clearSelectedAnnotations()

    $scope.dialog = visible: false

    $scope.search =
      query: $location.search()['q']

      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          $location.search('q', query or null)
          annotationUI.clearSelectedAnnotations()

    $scope.sort = name: 'Location'
    $scope.threading = threading
    $scope.threadRoot = $scope.threading?.root


class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'streamer', 'store', 'streamfilter', 'annotationMapper'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     streamer,   store,   streamfilter,   annotationMapper
  ) ->
    # Tells the view that these annotations are standalone
    $scope.isEmbedded = false
    $scope.isStream = false

    # Provide no-ops until these methods are moved elsewere. They only apply
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

    streamfilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.send({filter: streamfilter.getFilter()})

class ViewerController
  this.$inject = [
    '$scope', '$route', 'annotationUI', 'crossframe', 'annotationMapper',
    'auth', 'streamer', 'streamfilter', 'store'
  ]
  constructor:   (
     $scope,   $route, annotationUI, crossframe, annotationMapper,
     auth,   streamer,   streamfilter,   store
  ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

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
      if annotationUI.tool is 'highlight'
        return unless auth.user
        query.user = auth.user

      for p in crossframe.providers
        for e in p.entities when e not in loaded
          loaded.push e
          q = angular.extend(uri: e, query)
          _loadAnnotationsFrom q, 0

      streamfilter.resetFilter().addClause('/uri', 'one_of', loaded)

      if auth.user and annotationUI.tool is 'highlight'
        streamfilter.addClause('/user', 'equals', auth.user)

      streamer.send({filter: streamfilter.getFilter()})

    $scope.$watch (-> annotationUI.tool), (newVal, oldVal) ->
      return if newVal is oldVal
      $route.reload()

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
      annotation?.$$tag in ($scope.focusedAnnotations ? [])

angular.module('h')
.controller('AppController', AppController)
.controller('ViewerController', ViewerController)
.controller('AnnotationViewerController', AnnotationViewerController)
.controller('AnnotationUIController', AnnotationUIController)
