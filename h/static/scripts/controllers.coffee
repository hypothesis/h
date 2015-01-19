class UISyncController
  constructor: (@appScope, @crossFrameUI) ->
    @appScope.$on('showAnnotations', this._onShowAnnotations)
    @appScope.$on('focusAnnotations', this._onFocusAnnotations)
    @appScope.$on('toggleAnnotationSelection', this._onToggleAnnotationSelection)
    @appScope.$on('getDocumentInfo', this._onGetDocumentInfo)
    @appScope.$on('annotationsLoaded', this._onAnnotationsLoaded)

  _getAnnotationsForTags: (event, tags) ->
    tags.map(@crossFrameUI.getAnnotationForTag, @crossFrameUI)

  # Properly set the selectedAnnotations- and the Count variables
  _setSelectedAnnotations: (event, selected) ->
    count = Object.keys(selected).length
    @appScope.selectedAnnotationsCount = count

    if count
      @appScope.selectedAnnotations = selected
    else
      @appScope.selectedAnnotations = null

  _onToggleAnnotationSelection: (event, annotations=[]) ->
    @appScope.search.query = ''

    selected = @appScope.selectedAnnotations or {}
    for a in annotations
      if selected[a.id]
        delete selected[a.id]
      else
        selected[a.id] = true
    @_setSelectedAnnotations(selected)
    this

  _onFocusAnnotations: (event, tags) ->
    @appScope.focusedAnnotations = tags

  _onShowAnnotations: (event, tags) ->
    annotations = this._getAnnotationsForTags(tags)
    @appScope.search.query = ''
    selected = {}
    for a in annotations
      selected[a.id] = true
    @_setSelectedAnnotations selected

  _onAnnotationDeleted: (event, tag) =>
    annotation = this._getAnnotationForTags([tag])[0]
    if scope.selectedAnnotations?[annotation.id]
      delete @appScope.selectedAnnotations[annotation.id]
      @_setSelectedAnnotations(@appScope.selectedAnnotations)

  _onGetDocumentInfo: =>
    @appScope.$digest()
    @appScope.$evalAsync(angular.noop)

  _onAnnotationsLoaded: (event, annotations) =>
    @appScope.$evalAsync(angular.noop)


class AppController
  this.$inject = [
    '$document', '$location', '$route', '$scope', '$window', '$rootScope',
    'auth', 'documentHelpers', 'drafts', 'identity',
    'permissions', 'streamer', 'streamfilter', 'crossFrameUI',
    'annotationMapper', 'threading'
  ]
  constructor: (
     $document,   $location,   $route,   $scope,   $window, $rootScope,
     auth,   documentHelpers,   drafts,   identity,
     permissions,   streamer,   streamfilter, crossFrameUI,
     annotationMapper, threading
  ) ->
    uiSyncController = new UISyncController($rootScope, crossFrameUI)

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
            $rootScope.$emit('annotationDeleted', annotation)

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
        if crossFrameUI.tool is 'highlight' and annotation.user != auth.user
          $rootScope.$emit('annotationDeleted', container.message)
          drafts.remove annotation
        # Remove annotations the user is not authorized to view.
        else if not permissions.permits 'read', container.message, auth.user
          $rootScope.$emit('annotationDeleted', container.message)
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
        $rootScope.$emit('beforeAnnotationCreated', draft)

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
      $scope.selectedAnnotations = null
      $scope.selectedAnnotationsCount = 0

    $scope.dialog = visible: false

    $scope.search =
      query: $location.search()['q']

      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          $location.search('q', query or null)
          delete $scope.selectedAnnotations
          delete $scope.selectedAnnotationsCount

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
    '$scope', '$route', 'crossFrameUI', 'annotationMapper',
    'auth', 'flash', 'streamer', 'streamfilter', 'store'
  ]
  constructor:   (
     $scope,   $route, crossFrameUI, annotationMapper,
     auth,   flash,   streamer,   streamfilter,   store
  ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    loaded = []

    loadAnnotations = ->
      query = limit: 200
      if crossFrameUI.tool is 'highlight'
        return unless auth.user
        query.user = auth.user

      for p in crossFrameUI.providers
        for e in p.entities when e not in loaded
          loaded.push e
          r = store.SearchResource.get angular.extend(uri: e, query), (results) ->
            annotationMapper.loadAnnotations(results.rows)

      streamfilter.resetFilter().addClause('/uri', 'one_of', loaded)

      if auth.user and crossFrameUI.tool is 'highlight'
        streamfilter.addClause('/user', auth.user)

      streamer.send({filter: streamfilter.getFilter()})

    $scope.$watch (-> crossFrameUI.tool), (newVal, oldVal) ->
      return if newVal is oldVal
      $route.reload()

    $scope.$watchCollection (-> crossFrameUI.providers), loadAnnotations

    $scope.focus = (annotation) ->
      if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in crossFrameUI.providers
        p.channel.notify
          method: 'focusAnnotations'
          params: highlights

    $scope.scrollTo = (annotation) ->
      if angular.isObject annotation
        for p in crossFrameUI.providers
          p.channel.notify
            method: 'scrollToAnnotation'
            params: annotation.$$tag

    $scope.shouldShowThread = (container) ->
      if $scope.selectedAnnotations? and not container.parent.parent
        $scope.selectedAnnotations[container.message?.id]
      else
        true

    $scope.hasFocus = (annotation) ->
      annotation?.$$tag in ($scope.focusedAnnotations ? [])

angular.module('h')
.controller('AppController', AppController)
.controller('ViewerController', ViewerController)
.controller('AnnotationViewerController', AnnotationViewerController)
