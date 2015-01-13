class AppController
  this.$inject = [
    '$location', '$route', '$scope', '$timeout', '$window',
    'annotator', 'auth', 'documentHelpers', 'drafts', 'identity',
    'permissions', 'streamer', 'streamfilter'
  ]
  constructor: (
     $location,   $route,   $scope,   $timeout,   $window,
     annotator,   auth,   documentHelpers,   drafts,   identity,
     permissions,   streamer,   streamfilter,

  ) ->
    {plugins, host, providers} = annotator

    $scope.auth = auth
    isFirstRun = $location.search().hasOwnProperty('firstrun')
    streamerUrl = documentHelpers.baseURI.replace(/^http/, 'ws') + 'ws'

    applyUpdates = (action, data) ->
      # Update the application with new data from the websocket.
      return unless data?.length
      switch action
        when 'create', 'update', 'past'
          annotator.loadAnnotations data
        when 'delete'
          for annotation in data
            annotator.publish 'annotationDeleted', (annotation)

    streamer.onmessage = (data) ->
      return if !data or data.type != 'annotation-notification'
      action = data.options.action
      payload = data.payload
      applyUpdates(action, payload)
      $scope.$digest()

    oncancel = ->
      $scope.dialog.visible = false

    $scope.$on '$routeChangeStart', (event, newRoute, oldRoute) ->
      return if newRoute.redirectTo
      # Clean up any annotations that need to be unloaded.
      for id, container of $scope.threading.idTable when container.message
        # Remove annotations not belonging to this user when highlighting.
        if annotator.tool is 'highlight' and annotation.user != auth.user
          annotator.publish 'annotationDeleted', container.message
          drafts.remove annotation
        # Remove annotations the user is not authorized to view.
        else if not permissions.permits 'read', container.message, auth.user
          annotator.publish 'annotationDeleted', container.message
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

      # Skip the remaining if this is the first evaluation.
      return if oldVal is undefined

      # Update any edits in progress.
      for draft in drafts.all()
        annotator.publish 'beforeAnnotationCreated', draft

      # Reopen the streamer.
      streamer.close()
      streamer.open($window.WebSocket, streamerUrl)

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
      unless streamfilter.getPastData().hits then return
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
    $scope.threading = plugins.Threading


class AnnotationViewerController
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator', 'streamer', 'store', 'streamfilter'
  ]
  constructor: (
     $location,   $routeParams,   $scope,
     annotator,   streamer,   store,   streamfilter
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
    store.search.get _id: $routeParams.id, ({rows}) ->
      annotator.loadAnnotations(rows)
    store.search.get references: $routeParams.id, ({rows}) ->
      annotator.loadAnnotations(rows)

    streamfilter
      .setPastDataNone()
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'first_of', id, true)
      .addClause('/id', 'equals', id, true)

    streamer.send({filter: streamfilter.getFilter()})

class ViewerController
  this.$inject = [
    '$scope', '$route',
    'annotator', 'auth', 'flash', 'streamer', 'streamfilter', 'store'
  ]
  constructor:   (
     $scope,   $route,
     annotator,   auth,   flash,   streamer,   streamfilter,   store
  ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    loaded = []

    loadAnnotations = ->
      if annotator.tool is 'highlight'
        return unless auth.user
        query = user: auth.user

      for p in annotator.providers
        for e in p.entities when e not in loaded
          loaded.push e
          store.search.get angular.extend(uri: e, query), (results) ->
            annotator.loadAnnotations(results.rows)

      streamfilter.resetFilter().addClause('/uri', 'one_of', loaded)

      if auth.user and annotator.tool is 'highlight'
        streamfilter.addClause('/user', auth.user)

      streamer.send({filter: streamfilter.getFilter()})

    $scope.$watch (-> annotator.tool), (newVal, oldVal) ->
      return if newVal is oldVal
      $route.reload()

    $scope.$watchCollection (-> annotator.providers), loadAnnotations

    $scope.focus = (annotation) ->
      if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in annotator.providers
        p.channel.notify
          method: 'focusAnnotations'
          params: highlights

    $scope.scrollTo = (annotation) ->
      if angular.isObject annotation
        for p in annotator.providers
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
