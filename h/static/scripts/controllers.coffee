imports = [
  'bootstrap'
  'h.flash'
  'h.helpers.documentHelpers'
  'h.identity'
  'h.services'
  'h.socket'
  'h.searchfilters'
]


class App
  this.$inject = [
    '$location', '$q', '$route', '$scope', '$timeout',
    'annotator', 'flash', 'identity', 'socket', 'streamfilter',
    'documentHelpers', 'drafts'
  ]
  constructor: (
     $location,   $q,   $route,   $scope,   $timeout
     annotator,   flash,   identity,   socket,   streamfilter,
     documentHelpers,   drafts
  ) ->
    {plugins, host, providers} = annotator

    # Verified user id.
    # Undefined means we don't track the session, but the identity module will
    # tell us the state of the session. A null value means that the session
    # has been checked and it was found that there is no user logged in.
    loggedInUser = undefined

    # Resolved once the API service has been discovered.
    storeReady = $q.defer()

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

    initIdentity = (persona) ->
      """Initialize identity callbacks."""
      # Store the argument as the claimed user id.
      claimedUser = persona

      # Convert it to the format used by persona.
      if claimedUser then claimedUser = claimedUser.replace(/^acct:/, '')

      if claimedUser is loggedInUser
        if loggedInUser is undefined
          # This is the first execution.
          # Configure the identity callbacks and the initial user id claim.
          identity.watch
            loggedInUser: claimedUser
            onlogin: (assertion) ->
              onlogin(assertion)
            onlogout: ->
              onlogout()
      else if drafts.discard()
        if claimedUser
          identity.request()
        else
          identity.logout()

    initStore = ->
      """Initialize the storage component."""
      Store = plugins.Store
      delete plugins.Store
      annotator.addPlugin 'Store', annotator.options.Store

      $scope.store = plugins.Store

      _id = $route.current.params.id
      _promise = null

      # Load any initial annotations that should be displayed
      if _id
        # XXX: Two requests here is less than ideal
        plugins.Store.loadAnnotationsFromSearch({_id}).then ->
          plugins.Store.loadAnnotationsFromSearch({references: _id})

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
      user = $scope.persona
      cull = (acc, annotation) ->
        if annotator.tool is 'highlight' and annotation.user != user
          acc.drop.push annotation
        else if plugins.Permissions.authorize('read', annotation, user)
          acc.keep.push annotation
        else
          acc.drop.push annotation
        acc

      {keep, drop} = Store.annotations.reduce cull, {keep: [], drop: []}
      Store.annotations = []
      plugins.Store.annotations = keep

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
        #console.log msg
        unless msg.data.type? and msg.data.type is 'annotation-notification'
          return
        data = msg.data.payload
        action = msg.data.options.action

        unless data instanceof Array then data = [data]

        p = $scope.persona
        user = if p? then "acct:" + p.username + "@" + p.provider else ''
        unless data instanceof Array then data = [data]

        if $scope.socialView.name is 'single-player'
          owndata = data.filter (d) -> d.user is user
          applyUpdates action, owndata
        else
          applyUpdates action, data

        $scope.$digest()

      _dfdSock.promise

    onlogin = (assertion) ->
      # Delete any old Auth plugin.
      plugins.Auth?.destroy()
      delete plugins.Auth

      # Configure the Auth plugin with the issued assertion as refresh token.
      annotator.addPlugin 'Auth',
        tokenUrl: documentHelpers.absoluteURI(
          "/api/token?assertion=#{assertion}")

      # Set the user from the token.
      plugins.Auth.withToken (token) ->
        plugins.Permissions._setAuthFromToken(token)
        loggedInUser = plugins.Permissions.user.replace /^acct:/, ''
        reset()

    onlogout = ->
      plugins.Auth?.element.removeData('annotator:headers')
      delete plugins.Auth

      plugins.Permissions.setUser(null)

      # XXX: Temporary workaround until Annotator v2.0 or v1.2.10
      plugins.Permissions.options.permissions =
        read: []
        update: []
        delete: []
        admin: []

      loggedInUser = null
      reset()

    reset = ->
      # Do not rely on the identity service to invoke callbacks within an
      # angular digest cycle.
      $scope.$evalAsync ->
        if $scope.ongoingHighlightSwitch
          $scope.ongoingHighlightSwitch = false
          annotator.setTool 'highlight'
        else
          annotator.setTool 'comment'

        # Convert the verified user id to the format used by the API.
        persona = loggedInUser
        if persona then persona = "acct:#{persona}"

        # Ensure it is synchronized on the scope.
        # Without this, failed identity changes will remain on the scope.
        $scope.persona = persona

        # Reload services
        storeReady.promise.then ->
          initStore()
          initUpdater()

    annotator.subscribe 'annotationCreated', (annotation) ->
      if annotation is $scope.ongoingEdit?.message
        delete $scope.ongoingEdit
        for p in providers
          p.channel.notify method: 'onEditorSubmit'
          p.channel.notify method: 'onEditorHide'

    annotator.subscribe 'annotationDeleted', (annotation) ->
      if annotation is $scope.ongoingEdit?.message
        delete $scope.ongoingEdit
        for p in providers
          p.channel.notify method: 'onEditorHide'

    annotator.subscribe 'serviceDiscovery', (options) ->
      annotator.options.Store ?= {}
      angular.extend annotator.options.Store, options
      storeReady.resolve()

    $scope.$watch 'persona', initIdentity

    $scope.$watch 'socialView.name', (newValue, oldValue) ->
      return if newValue is oldValue

      if $scope.persona
        initStore()
      else if newValue is 'single-player'
        identity.request()

    $scope.$watch 'frame.visible', (newValue, oldValue) ->
      if newValue
        annotator.show()
        annotator.host.notify method: 'showFrame'
      else if oldValue
        annotator.hide()
        annotator.host.notify method: 'hideFrame'
        for p in annotator.providers
          p.channel.notify method: 'setActiveHighlights'

    $scope.$watch 'sort.name', (name) ->
      return unless name
      [predicate, reverse] = switch name
        when 'Newest' then ['message.updated', true]
        when 'Oldest' then ['message.updated', false]
        when 'Location' then ['message.target[0].pos.top', false]
      $scope.sort = {name, predicate, reverse}

    $scope.$watch 'store.entities', (entities, oldEntities) ->
      return if entities is oldEntities

      if entities.length
        streamfilter
          .resetFilter()
          .addClause('/uri', 'one_of', entities)

        $scope.updater.then (sock) ->
          filter = streamfilter.getFilter()
          sock.send(JSON.stringify({filter}))

    $scope.loadMore = (number) ->
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.then (sock) ->
        sock.send(JSON.stringify(sockmsg))

    $scope.authTimeout = ->
      delete $scope.ongoingEdit
      $scope.ongoingHighlightSwitch = false
      flash 'info',
        'For your security, the forms have been reset due to inactivity.'

    $scope.clearSelection = ->
      $scope.search.query = ''
      $scope.selectedAnnotations = null
      $scope.selectedAnnotationsCount = 0

    $scope.baseURI = documentHelpers.baseURI
    $scope.frame = visible: false
    $scope.id = identity

    $scope.model = persona: undefined
    $scope.threading = plugins.Threading

    $scope.search =
      query: $location.search()['q']

      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          if drafts.discard()
            $location.search('q', query or null)

    $scope.socialView = annotator.socialView
    $scope.sort = name: 'Location'


class AnnotationViewer
  this.$inject = ['$routeParams', '$scope', 'streamfilter']
  constructor: ($routeParams, $scope, streamfilter) ->
    # Tells the view that these annotations are standalone
    $scope.isEmbedded = false
    $scope.isStream = false

    # Provide no-ops until these methods are moved elsewere. They only apply
    # to annotations loaded into the stream.
    $scope.activate = angular.noop

    $scope.shouldShowThread = -> true

    $scope.$watch 'updater', (updater) ->
      if updater?
        updater.then (sock) ->
          filter = streamfilter
            .setPastDataNone()
            .setMatchPolicyIncludeAny()
            .addClause('/references', 'first_of', $routeParams.id, true)
            .addClause('/id', 'equals', $routeParams.id, true)
            .getFilter()
          sock.send(JSON.stringify({filter}))


class Viewer
  this.$inject = [
    '$filter', '$routeParams', '$sce', '$scope',
    'annotator', 'searchfilter', 'viewFilter'
  ]
  constructor: (
     $filter,   $routeParams,   $sce,   $scope,
     annotator,   searchfilter,   viewFilter
  ) ->
    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    $scope.activate = (annotation) ->
      if angular.isObject annotation
        highlights = [annotation.$$tag]
      else if $scope.ongoingEdit
        highlights = [$scope.ongoingEdit.message.$$tag]
      else
        highlights = []
      for p in annotator.providers
        p.channel.notify
          method: 'setActiveHighlights'
          params: highlights

    $scope.shouldShowThread = (container) ->
      if $routeParams.q
        container.shown
      else if $scope.selectedAnnotations?
        $scope.selectedAnnotations[container.message?.id]
      else
        true

    $scope.showMoreTop = (container) ->
      rendered = container.renderOrder
      pos = rendered.indexOf(container)
      container.moreTop = 0

      while --pos >= 0
        prev = rendered[pos]
        prev.moreBottom = 0
        break if prev.shown
        prev.moreTop = 0
        prev.shown = true

    $scope.showMoreBottom = (container) ->
      $event?.stopPropagation()
      rendered = container.renderOrder
      pos = rendered.indexOf(container)
      container.moreBottom = 0

      while ++pos < rendered.length
        next = rendered[pos]
        next.moreTop = 0
        break if next.shown
        next.moreBottom = 0
        next.shown = true

    matches = null
    orderBy = $filter('orderBy')

    render = (thread, last, current) ->
      current.renderOrder = thread.renderOrder
      current.shown = matches[current.message?.id]?

      order = thread.renderOrder.length
      thread.renderOrder.push current

      if current.shown
        current.renderOrder[last].moreBottom = 0
        current.moreTop = order - last - 1
        current.moreBottom = 0
        last = order
      else if last != order
        current.moreTop = 0
        current.moreBottom = 0
        current.renderOrder[last].moreBottom++

      sorted = orderBy (current.children or []), 'message.updated'
      sorted.reduce(angular.bind(null, render, thread), last)

    refresh = ->
      annotations = $scope.threading.root.flattenChildren() or []
      matches = {}
      rendered = {}
      query = $routeParams.q

      if query
        # Get the set of matches
        filters = searchfilter.generateFacetedFilter query
        for match in viewFilter.filter annotations, filters
          matches[match] = true

        # Find the top posts and render them
        for annotation in annotations
          {id, references} = annotation
          if typeof(references) == 'string' then references = [references]
          if matches[id]?
            top = references?[0] or id
            continue if rendered[top]
            container = $scope.threading.getContainer(top)
            container.renderOrder = []
            render container, 0, container
            container.shown = true
            rendered[id] = true
          else
            container = $scope.threading.getContainer(annotation.id)
            container.shown = false
      else
        for annotation in annotations
          container = $scope.threading.getContainer(annotation.id)
          angular.extend container,
            moreTop: 0
            moreBottom: 0
            renderOrder: null
            shown: true

      $scope.matches = Object.keys(matches).length
      delete $scope.selectedAnnotations


    $scope.$on '$routeChangeSuccess', refresh
    $scope.$on '$routeUpdate', refresh


angular.module('h.controllers', imports)
.controller('AppController', App)
.controller('ViewerController', Viewer)
.controller('AnnotationViewerController', AnnotationViewer)
