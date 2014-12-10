class AppController
  this.$inject = [
    '$location', '$q', '$route', '$scope', '$timeout',
    'annotator', 'flash', 'socket', 'streamfilter',
    'drafts', 'auth'
  ]
  constructor: (
     $location,   $q,   $route,   $scope,   $timeout,
     annotator,   flash,   socket,   streamfilter,
     drafts,   auth
  ) ->
    {plugins, host, providers} = annotator

    applyUpdates = (action, data) ->
      """Update the application with new data from the websocket."""
      return unless data?.length
      if action == 'past'
        action = 'create'

      switch action
        when 'create', 'update'
          plugins.Store?._onLoadAnnotations data
        when 'delete'
          for annotation in data
            annotation = plugins.Threading.idTable[annotation.id]?.message
            continue unless annotation?
            plugins.Store?.unregisterAnnotation(annotation)
            annotator.deleteAnnotation(annotation)

    initStore = ->
      """Initialize the storage component."""
      Store = plugins.Store
      delete plugins.Store

      if auth.user or annotator.socialView.name is 'none'
        annotator.addPlugin 'Store', annotator.options.Store

        $scope.store = plugins.Store

      return unless Store
      Store.destroy()

      # XXX: Hacky hacky stuff to ensure that any search requests in-flight
      # at this time have no effect when they resolve and that future events
      # have no effect on this Store. Unfortunately, it's not possible to
      # unregister all the events or properly unload the Store because the
      # registration loses the closure. The approach here is perhaps
      # cleaner than fishing them out of the jQuery private data.
      # * Overwrite the Store's handle to the annotator, giving it one
      #   with a noop `loadAnnotations` method.
      Store.annotator = loadAnnotations: angular.noop
      # * Make all api requests into a noop.
      Store._apiRequest = angular.noop
      # * Ignore pending searches
      Store._onLoadAnnotations = angular.noop
      # * Make the update function into a noop.
      Store.updateAnnotation = angular.noop

      # Sort out which annotations should remain in place.
      persona = auth.user
      view = annotator.socialView.name
      cull = (acc, annotation) ->
        if view is 'single-player' and annotation.user != persona
          acc.drop.push annotation
        else if auth.permits 'read', annotation, persona
          acc.keep.push annotation
        else
          acc.drop.push annotation
        acc

      {keep, drop} = Store.annotations.reduce cull, {keep: [], drop: []}
      Store.annotations = []

      if plugins.Store?
        plugins.Store.annotations = keep
      else
        drop = drop.concat keep

      # Clean up the ones that should be removed.
      do cleanup = (drop) ->
        return if drop.length == 0
        [first, rest...] = drop
        annotator.deleteAnnotation first
        $timeout -> cleanup rest

    initUpdater = (failureCount=0) ->
      """Initialize the websocket used for realtime updates."""
      _dfdSock = $q.defer()
      _sock = socket()

      $scope.updater?.then (sock) ->
        sock.onclose = null  # break automatic reconnect
        sock.close()

      $scope.updater = _dfdSock.promise

      _sock.onopen = ->
        failureCount = 0
        _dfdSock.resolve(_sock)
        _dfdSock = null

      _sock.onclose = ->
        failureCount = Math.min(10, ++failureCount)
        slots = Math.random() * (Math.pow(2, failureCount) - 1)
        $timeout ->
          _retry = initUpdater(failureCount)
          _dfdSock?.resolve(_retry)
        , slots * 500

      _sock.onmessage = (msg) ->
        unless msg.data.type? and msg.data.type is 'annotation-notification'
          return
        data = msg.data.payload
        action = msg.data.options.action

        unless data instanceof Array then data = [data]

        p = auth.user
        user = if p? then "acct:" + p.username + "@" + p.provider else ''
        unless data instanceof Array then data = [data]

        if $scope.socialView.name is 'single-player'
          owndata = data.filter (d) -> d.user is user
          applyUpdates action, owndata
        else
          applyUpdates action, data

        $scope.$digest()

      _dfdSock.promise

    oncancel = ->
      $scope.dialog.visible = false

    reset = ->
      $scope.persona = auth.user
      $scope.dialog.visible = false

      # Update any edits in progress.
      for draft in drafts.all()
        annotator.publish 'beforeAnnotationCreated', draft

      # Reload services
      initStore()
      initUpdater()

    $scope.$watch 'socialView.name', (newValue, oldValue) ->
      return if newValue is oldValue
      initStore()
      if newValue is 'single-player' and not auth.user
        annotator.show()
        flash 'info',
          'You will need to sign in for your highlights to be saved.'

    $scope.$watch 'sort.name', (name) ->
      return unless name
      predicate = switch name
        when 'Newest' then ['-!!message', '-message.updated']
        when 'Oldest' then ['-!!message',  'message.updated']
        when 'Location' then ['-!!message', 'message.target[0].pos.top']
      $scope.sort = {name, predicate}

    $scope.$watch 'store.entities', (entities, oldEntities) ->
      return if entities is oldEntities or not entities

      if entities.length
        streamfilter
          .resetFilter()
          .addClause('/uri', 'one_of', entities)

        $scope.updater.then (sock) ->
          filter = streamfilter.getFilter()
          sock.send(JSON.stringify({filter}))

    $scope.login = ->
      $scope.dialog.visible = true
      auth.login().then(reset, oncancel)

    $scope.logout = ->
      return unless drafts.discard()
      $scope.dialog.visible = false
      auth.logout().then(reset)

    $scope.loadMore = (number) ->
      unless streamfilter.getPastData().hits then return
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.then (sock) ->
        sock.send(JSON.stringify(sockmsg))

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

    $scope.socialView = annotator.socialView
    $scope.sort = name: 'Location'
    $scope.threading = plugins.Threading

    auth.getInitialUser().then(reset, ->
      reset()
      $scope.login()
    )


class AnnotationViewerController
  this.$inject = ['$location', '$routeParams', '$scope', 'annotator', 'streamfilter']
  constructor: ($location, $routeParams, $scope, annotator, streamfilter) ->
    # Tells the view that these annotations are standalone
    $scope.isEmbedded = false
    $scope.isStream = false

    # Clear out loaded annotations and threads
    # XXX: Resolve threading, storage, and updater better for all routes.
    annotator.plugins.Threading?.pluginInit()
    annotator.plugins.Store?.annotations = []

    # Provide no-ops until these methods are moved elsewere. They only apply
    # to annotations loaded into the stream.
    $scope.focus = angular.noop

    $scope.shouldShowThread = -> true

    $scope.search.update = (query) ->
      $location.path('/stream').search('q', query)

    $scope.$watch 'updater', (updater) ->
      if updater?
        updater.then (sock) ->
          if $routeParams.id?
            _id = $routeParams.id
            annotator.plugins.Store?.loadAnnotationsFromSearch({_id}).then ->
              annotator.plugins.Store?.loadAnnotationsFromSearch({references: _id})

            filter = streamfilter
              .setPastDataNone()
              .setMatchPolicyIncludeAny()
              .addClause('/references', 'first_of', _id, true)
              .addClause('/id', 'equals', _id, true)
              .getFilter()
            sock.send(JSON.stringify({filter}))

class ViewerController
  this.$inject = ['$scope', 'annotator']
  constructor:   ( $scope,   annotator ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

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
