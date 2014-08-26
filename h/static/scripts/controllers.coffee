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
    'documentHelpers'
  ]
  constructor: (
     $location,   $q,   $route,   $scope,   $timeout
     annotator,   flash,   identity,   socket,   streamfilter,
     documentHelpers
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
            container = annotator.threading.getContainer annotation.id
            if container.message
              # XXX: This is a temporary workaround until real client-side only
              # XXX: delete will be introduced
              index = plugins.Store.annotations.indexOf container.message
              plugins.Store.annotations[index..index] = [] if index > -1
              annotator.deleteAnnotation container.message

      $scope.$digest()

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
      else if annotator.discardDrafts()
        if claimedUser
          identity.request()
        else
          identity.logout()

    initStore = ->
      """Initialize the storage component."""
      Store = plugins.Store
      delete plugins.Store
      delete $scope.threadRoot
      annotator.addPlugin 'Store', annotator.options.Store

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
      unless annotation.thread.parent
        $scope.threadRoot.addChild annotation.thread

      if annotation is $scope.ongoingEdit
        delete $scope.ongoingEdit
        for p in providers
          p.channel.notify method: 'onEditorSubmit'
          p.channel.notify method: 'onEditorHide'

    annotator.subscribe 'annotationDeleted', (annotation) ->
      if annotation is $scope.ongoingEdit
        delete $scope.ongoingEdit
        for p in providers
          p.channel.notify method: 'onEditorHide'

    annotator.subscribe 'annotationsLoaded', (annotations) ->
      $scope.threadRoot ?= annotator.threading.thread(annotations)
      $scope.$digest()

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
      routeName = $location.path().replace /^\//, ''
      if newValue
        annotator.show()
        annotator.host.notify method: 'showFrame', params: routeName
      else if oldValue
        annotator.hide()
        annotator.host.notify method: 'hideFrame', params: routeName
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

    $scope.frame = visible: false
    $scope.id = identity

    $scope.model = persona: undefined

    $scope.search =
      query: $location.search()['q']

      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          if annotator.discardDrafts()
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

    $scope.shouldShowAnnotation = (id) -> true

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
    '$location', '$routeParams', '$scope', 'annotator'
  ]
  constructor: ($location, $routeParams, $scope, annotator) ->
    if $routeParams.q
      return $location.path('/page_search').replace()

    # Tells the view that these annotations are embedded into the owner doc
    $scope.isEmbedded = true
    $scope.isStream = true

    {providers, threading} = annotator

    $scope.activate = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in providers
        p.channel.notify
          method: 'setActiveHighlights'
          params: highlights

    $scope.shouldShowAnnotation = (id) ->
      selectedAnnotations = $scope.selectedAnnotations
      !selectedAnnotations or selectedAnnotations?[id]


class Search
  this.$inject = ['$filter', '$location', '$routeParams', '$sce', '$scope',
                  'annotator', 'viewFilter']
  constructor: ($filter, $location, $routeParams, $sce, $scope,
                annotator, viewFilter) ->
    unless $routeParams.q
      return $location.path('/viewer').replace()

    {providers, threading} = annotator

    $scope.isEmbedded = true
    $scope.isStream = true

    $scope.highlighter = '<span class="search-hl-active">$&</span>'
    $scope.filter_orderBy = $filter('orderBy')
    $scope.matches = []
    $scope.render_order = {}
    $scope.render_pos = {}
    $scope.ann_info =
      shown : {}
      show_quote: {}
      more_top : {}
      more_bottom : {}
      more_top_num : {}
      more_bottom_num: {}

    $scope.shouldShowAnnotation = (id) ->
      shownAnnotations = $scope.ann_info?.shown or {}
      !!shownAnnotations[id]

    buildRenderOrder = (threadid, threads) =>
      unless threads?.length
        return

      sorted = $scope.filter_orderBy threads, $scope.sortThread, true
      for thread in sorted
        $scope.render_pos[thread.message.id] = $scope.render_order[threadid].length
        $scope.render_order[threadid].push thread.message.id
        buildRenderOrder(threadid, thread.children)

    setMoreTop = (threadid, annotation) =>
      unless annotation.id in $scope.matches
        return false

      result = false
      pos = $scope.render_pos[annotation.id]
      if pos > 0
        prev = $scope.render_order[threadid][pos-1]
        unless prev in $scope.matches
          result = true
      result

    setMoreBottom = (threadid, annotation) =>
      unless annotation.id in $scope.matches
        return false

      result = false
      pos = $scope.render_pos[annotation.id]

      if pos < $scope.render_order[threadid].length-1
        next = $scope.render_order[threadid][pos+1]
        unless next in $scope.matches
          result = true
      result

    $scope.activate = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in providers
        p.channel.notify
          method: 'setActiveHighlights'
          params: highlights

    $scope.$watch 'annotations', (nVal, oVal) =>
      refresh()

    refresh = =>
      query = $routeParams.q
      annotations = $scope.threadRoot.flattenChildren()
      [$scope.matches, $scope.filters] = viewFilter.filter annotations, query
      # Create the regexps for highlighting the matches inside the annotations' bodies
      $scope.text_tokens = $scope.filters.text.terms.slice()
      $scope.text_regexp = []
      $scope.quote_tokens = $scope.filters.quote.terms.slice()
      $scope.quote_regexp = []

      # Highligh any matches
      for term in $scope.filters.any.terms
        $scope.text_tokens.push term
        $scope.quote_tokens.push term

      # Saving the regexps and higlighter to the annotator for highlighttext regeneration
      for token in $scope.text_tokens
        regexp = new RegExp(token,"ig")
        $scope.text_regexp.push regexp

      for token in $scope.quote_tokens
        regexp = new RegExp(token,"ig")
        $scope.quote_regexp.push regexp

      annotator.text_regexp = $scope.text_regexp
      annotator.quote_regexp = $scope.quote_regexp
      annotator.highlighter = $scope.highlighter

      threads = []
      roots = {}
      $scope.render_order = {}

      # Choose the root annotations to work with
      for id, thread of annotator.threading.idTable when thread.message?
        annotation = thread.message
        annotation_root = if annotation.references? then annotation.references[0] else annotation.id
        # Already handled thread
        if roots[annotation_root]? then continue
        root_annotation = (annotator.threading.getContainer annotation_root).message
        unless root_annotation in annotations then continue

        if annotation.id in $scope.matches
          # We have a winner, let's put its root annotation into our list and build the rendering
          root_thread = annotator.threading.getContainer annotation_root
          threads.push root_thread
          $scope.render_order[annotation_root] = []
          buildRenderOrder(annotation_root, [root_thread])
          roots[annotation_root] = true

      # Re-construct exact order the annotation threads will be shown

      # Fill search related data before display
      # - add highlights
      # - populate the top/bottom show more links
      # - decide that by default the annotation is shown or hidden
      # - Open detail mode for quote hits
      for thread in threads
        thread.message.highlightText = thread.message.text
        if thread.message.id in $scope.matches
          $scope.ann_info.shown[thread.message.id] = true
          if thread.message.text?
            for regexp in $scope.text_regexp
              thread.message.highlightText = thread.message.highlightText.replace regexp, $scope.highlighter
        else
          $scope.ann_info.shown[thread.message.id] = false

        $scope.ann_info.more_top[thread.message.id] = setMoreTop(thread.message.id, thread.message)
        $scope.ann_info.more_bottom[thread.message.id] = setMoreBottom(thread.message.id, thread.message)

        if $scope.quote_tokens?.length > 0
          $scope.ann_info.show_quote[thread.message.id] = true
          for target in thread.message.target
            target.highlightQuote = target.quote
            for regexp in $scope.quote_regexp
              target.highlightQuote = target.highlightQuote.replace regexp, $scope.highlighter
            target.highlightQuote = $sce.trustAsHtml target.highlightQuote
            if target.diffHTML?
              target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
              target.showDiff = not target.diffCaseOnly
            else
              delete target.trustedDiffHTML
              target.showDiff = false
        else
          for target in thread.message.target
            target.highlightQuote = target.quote
          $scope.ann_info.show_quote[thread.message.id] = false


        children = thread.flattenChildren()
        if children?
          for child in children
            child.highlightText = child.text
            if child.id in $scope.matches
              $scope.ann_info.shown[child.id] = true
              for regexp in $scope.text_regexp
                child.highlightText = child.highlightText.replace regexp, $scope.highlighter
            else
              $scope.ann_info.shown[child.id] = false

            $scope.ann_info.more_top[child.id] = setMoreTop(thread.message.id, child)
            $scope.ann_info.more_bottom[child.id] = setMoreBottom(thread.message.id, child)

            $scope.ann_info.show_quote[child.id] = false


      # Calculate the number of hidden annotations for <x> more labels
      for threadid, order of $scope.render_order
        hidden = 0
        last_shown = null
        for id in order
          if id in $scope.matches
            if last_shown? then $scope.ann_info.more_bottom_num[last_shown] = hidden
            $scope.ann_info.more_top_num[id] = hidden
            last_shown = id
            hidden = 0
          else
            hidden += 1
        if last_shown? then $scope.ann_info.more_bottom_num[last_shown] = hidden

    $scope.$on '$routeUpdate', refresh

    $scope.getThreadId = (id) ->
      thread = annotator.threading.getContainer id
      threadid = id
      if thread.message.references?
        threadid = thread.message.references[0]
      threadid

    $scope.clickMoreTop = (id, $event) ->
      $event?.stopPropagation()
      threadid = $scope.getThreadId id
      pos = $scope.render_pos[id]
      rendered = $scope.render_order[threadid]
      $scope.ann_info.more_top[id] = false

      pos -= 1
      while pos >= 0
        prev_id = rendered[pos]
        if $scope.ann_info.shown[prev_id]
          $scope.ann_info.more_bottom[prev_id] = false
          break
        $scope.ann_info.more_bottom[prev_id] = false
        $scope.ann_info.more_top[prev_id] = false
        $scope.ann_info.shown[prev_id] = true
        pos -= 1


    $scope.clickMoreBottom = (id, $event) ->
      $event?.stopPropagation()
      threadid = $scope.getThreadId id
      pos = $scope.render_pos[id]
      rendered = $scope.render_order[threadid]
      $scope.ann_info.more_bottom[id] = false

      pos += 1
      while pos < rendered.length
        next_id = rendered[pos]
        if $scope.ann_info.shown[next_id]
          $scope.ann_info.more_top[next_id] = false
          break
        $scope.ann_info.more_bottom[next_id] = false
        $scope.ann_info.more_top[next_id] = false
        $scope.ann_info.shown[next_id] = true
        pos += 1

    refresh()


angular.module('h.controllers', imports)
.controller('AppController', App)
.controller('ViewerController', Viewer)
.controller('AnnotationViewerController', AnnotationViewer)
.controller('SearchController', Search)
