imports = [
  'bootstrap'
  'h.flash'
  'h.helpers'
  'h.identity'
  'h.services'
  'h.socket'
  'h.searchfilters'
]

class App
  this.$inject = [
    '$element', '$location', '$q', '$rootScope', '$route', '$scope', '$timeout',
    'annotator', 'flash', 'identity', 'queryparser', 'socket',
    'streamfilter', 'viewFilter'
  ]
  constructor: (
     $element,   $location,   $q,   $rootScope,   $route,   $scope,   $timeout
     annotator,   flash,   identity,   queryparser,   socket,
     streamfilter,   viewFilter
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

      inRootScope = (annotation, recursive = false) ->
        if recursive and  annotation.references?
          return inRootScope({id: annotation.references[0]})
        for ann in $rootScope.annotations
          return true if ann.id is annotation.id
        false

      switch action
        when 'create'
          # Sorting the data for updates.
          # Because sometimes a reply can arrive in the same package as the
          # Root annotation, we have to make a len(references, updates sort
          data.sort (a,b) ->
            ref_a = a.references?.length or 0
            ref_b = b.references?.length or 0
            return ref_a - ref_b if ref_a != ref_b

            a_upd = if a.updated? then new Date(a.updated) else new Date()
            b_upd = if b.updated? then new Date(b.updated) else new Date()
            a_upd.getTime() - b_upd.getTime()

          # XXX: Temporary workaround until solving the race condition for annotationsLoaded event
          # Between threading and bridge plugins
          for annotation in data
            plugins.Threading.thread annotation

          if plugins.Store?
            plugins.Store._onLoadAnnotations data
            # XXX: Ugly workaround to update the scope content

            for annotation in data
              switch $rootScope.viewState.view
                when 'Document'
                  unless annotator.isComment(annotation)
                    $rootScope.annotations.push annotation if not inRootScope(annotation, true)
                when 'Comments'
                  if annotator.isComment(annotation)
                    $rootScope.annotations.push annotation if not inRootScope(annotation)
                else
                    $rootScope.annotations.push annotation if not inRootScope(annotation)
        when 'update'
          plugins.Store._onLoadAnnotations data

          if $location.path() is '/stream'
            for annotation in data
              $rootScope.annotations.push annotation if not inRootScope(annotation)
        when 'delete'
          for annotation in data
            # Remove it from the rootScope too
            for ann, index in $rootScope.annotations
              if ann.id is annotation.id
                $rootScope.annotations.splice(index, 1)
                break

            container = annotator.threading.getContainer annotation.id
            if container.message
              # XXX: This is a temporary workaround until real client-side only
              # XXX: delete will be introduced
              index = plugins.Store.annotations.indexOf container.message
              plugins.Store.annotations[index..index] = [] if index > -1
              annotator.deleteAnnotation container.message

      # Refresh page search
      $route.reload() if $location.path() is '/page_search' and data.length

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
      annotator.addPlugin 'Store', annotator.options.Store

      annotator.threading.thread []
      annotator.threading.idTable = {}

      $scope.$root.annotations = []
      $scope.store = plugins.Store

      _id = $route.current.params.id
      _promise = null

      # Load any initial annotations that should be displayed
      if _id
        if $scope.loadAnnotations
          # Load annotations from inline page data
          plugins.Store._onLoadAnnotations $scope.loadAnnotations
          delete $scope.loadAnnotations
          _promise = $scope.loadAnnotations
        else
          # Load annotations from the API
          # XXX: Two requests here is less than ideal
          _promise = plugins.Store.loadAnnotationsFromSearch({_id})
            .then ->
              plugins.Store.loadAnnotationsFromSearch({references: _id})

        $q.when _promise, ->
          thread = annotator.threading.getContainer _id
          $scope.$root.annotations = [thread.message]

      return unless Store

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
      # * Remove the plugin and re-add it to the annotator.

      # Even though most operations on the old Store are now noops the Annotator
      # itself may still be setting up previously fetched annotatiosn. We may
      # delete annotations which are later set up in the DOM again, causing
      # issues with the viewer and heatmap. As these are loaded, we can delete
      # them, but the threading plugin will get confused and break threading.
      # Here, we cleanup these annotations as they are set up by the Annotator,
      # preserving the existing threading. This is all a bit paranoid, but
      # important when many annotations are loading as authentication is
      # changing. It's all so ugly it makes me cry, though. Someone help
      # restore sanity?
      annotations = Store.annotations.slice()
      cleanup = (loaded) ->
        $timeout ->  # Give the threading plugin time to thread this annotation
          deleted = []
          for l in loaded
            if l in annotations
              # If this annotation still exists, we'll need to thread it again
              # since the delete will mangle the threading data structures.
              existing = annotator.threading.idTable[l.id]?.message
              annotator.deleteAnnotation(l)
              deleted.push l
              if existing
                plugins.Threading.thread existing
          annotations = (a for a in annotations when a not in deleted)
          if annotations.length is 0
            annotator.unsubscribe 'annotationsLoaded', cleanup
            $rootScope.$digest()
        , 10
      cleanup (a for a in annotations when a.thread)
      annotator.subscribe 'annotationsLoaded', cleanup

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
      delete plugins.Auth

      # Configure the Auth plugin with the issued assertion as refresh token.
      annotator.addPlugin 'Auth',
        tokenUrl: "#{baseURI}api/token?assertion=#{assertion}"

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
        if annotator.ongoing_edit
          annotator.clickAdder()

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

    $scope.$watch 'store.entities', (entities, oldEntities) ->
      return if entities is oldEntities

      if entities.length
        streamfilter
          .resetFilter()
          .addClause('/uri', 'one_of', entities)

      $scope.updater.then (sock) ->
        filter = streamfilter.getFilter()
        sock.send(JSON.stringify({filter}))

    $rootScope.viewState =
      sort: ''
      view: 'Screen'

    # Show the sort/view control for a while.
    #
    # hide: should we hide it after a second?
    _vstp = null
    $rootScope.showViewSort = (show = true, hide = false) ->
      if _vstp then $timeout.cancel _vstp
      $rootScope.viewState.showControls = show
      if $rootScope.viewState.showControls and hide
        _vstp = $timeout (-> $rootScope.viewState.showControls = false), 1000

    # "View" -- which annotations are shown
    $rootScope.applyView = (view) ->
      return if $rootScope.viewState.view is view
      $rootScope.viewState.view = view
      $rootScope.showViewSort true, true
      switch view
        when 'Screen'
          # Go over all providers, and switch them to dynamic mode
          # They will, in turn, call back updateView
          # with the right set of annotations
          for p in providers
            p.channel.notify method: 'setDynamicBucketMode', params: true

        when 'Document'
          for p in providers
            p.channel.notify method: 'showAll'

        when 'Comments'
          for p in providers
            p.channel.notify method: 'setDynamicBucketMode', params: false
          annotations = plugins.Store?.annotations
          comments = annotations.filter (a) -> annotator.isComment(a)
          $rootScope.annotations = comments

        when 'Selection'
          for p in providers
            p.channel.notify method: 'setDynamicBucketMode', params: false

        else
          throw new Error "Unknown view requested: " + view

    # "Sort" -- order annotations are shown
    $rootScope.applySort = (sort) ->
      return if $rootScope.viewState.sort is sort
      $rootScope.viewState.sort = sort
      $rootScope.showViewSort true, true
      switch sort
        when 'Newest'
          $rootScope.predicate = 'updated'
          $rootScope.searchPredicate = 'message.updated'
          $rootScope.reverse = true
        when 'Oldest'
          $rootScope.predicate = 'updated'
          $rootScope.searchPredicate = 'message.updated'
          $rootScope.reverse = false
        when 'Location'
          $rootScope.predicate = 'target[0].pos.top'
          $rootScope.searchPredicate = 'message.target[0].pos.top'
          $rootScope.reverse = false

    $rootScope.applySort "Location"

    $rootScope.$on '$routeChangeSuccess', (event, next, current) ->
      unless next.$$route? then return

      $scope.search.query = $location.search()['q']
      $rootScope.viewState.show = next.$$route.originalPath is '/viewer'

      unless next.$$route.originalPath is '/stream'
        if current and next.$$route.originalPath is '/a/:id'
          $scope.reloadAnnotations()

    $scope.loadMore = (number) ->
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.then (sock) ->
        sock.send(JSON.stringify(sockmsg))

    $scope.authTimeout = ->
      delete annotator.ongoing_edit
      $scope.ongoingHighlightSwitch = false
      flash 'info',
        'For your security, the forms have been reset due to inactivity.'

    $scope.frame = visible: false
    $scope.id = identity

    $scope.model = persona: undefined

    $scope.search =
      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          if annotator.discardDrafts()
            $location.search('q', query or null)

    $scope.socialView = annotator.socialView


class Annotation
  this.$inject = [
    '$element', '$location', '$rootScope', '$sce', '$scope', '$timeout',
    '$window',
    'annotator', 'baseURI', 'drafts'
  ]
  constructor: (
     $element,   $location,   $rootScope,   $sce,   $scope,   $timeout,
     $window,
     annotator,   baseURI,   drafts
  ) ->
    {plugins, threading} = annotator
    $scope.action = 'create'
    $scope.editing = false

    $scope.cancel = ($event) ->
      $event?.stopPropagation()
      $scope.editing = false
      drafts.remove $scope.model

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model
        else
          $scope.model.text = $scope.origText
          $scope.model.tags = $scope.origTags
          $scope.action = 'create'

    $scope.save = ($event) ->
      $event?.stopPropagation()
      annotation = $scope.model

      # Forbid saving comments without a body (text or tags)
      if annotator.isComment(annotation) and not annotation.text and
      not annotation.tags?.length
        $window.alert "You can not add a comment without adding some text, or at least a tag."
        return

      # Forbid the publishing of annotations
      # without a body (text or tags)
      if $scope.form.privacy.$viewValue is "Public" and
          $scope.action isnt "delete" and
          not annotation.text and not annotation.tags?.length
        $window.alert "You can not make this annotation public without adding some text, or at least a tag."
        return

      $scope.rebuildHighlightText()

      $scope.editing = false
      drafts.remove annotation

      switch $scope.action
        when 'create'
          # First, focus on the newly created annotation
          unless annotator.isReply annotation
            $rootScope.focus annotation, true

          if annotator.isComment(annotation) and
              $rootScope.viewState.view isnt "Comments"
            $rootScope.applyView "Comments"
          else if not annotator.isReply(annotation) and
              $rootScope.viewState.view not in ["Document", "Selection"]
            $rootScope.applyView "Screen"
          annotator.publish 'annotationCreated', annotation
        when 'delete'
          root = $scope.$root.annotations
          root = (a for a in root when a isnt root)
          annotation.deleted = true
          unless annotation.text? then annotation.text = ''
          annotator.updateAnnotation annotation
        else
          annotator.updateAnnotation annotation

    $scope.reply = ($event) ->
      $event?.stopPropagation()
      unless plugins.Auth? and plugins.Auth.haveValidToken()
        $window.alert "In order to reply, you need to sign in."
        return

      references =
        if $scope.thread.message.references
          [$scope.thread.message.references..., $scope.thread.message.id]
        else
          [$scope.thread.message.id]

      reply =
        references: references
        uri: $scope.thread.message.uri

      annotator.publish 'beforeAnnotationCreated', [reply]
      drafts.add reply
      return

    $scope.edit = ($event) ->
      $event?.stopPropagation()
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.text
      $scope.origTags = $scope.model.tags
      drafts.add $scope.model, -> $scope.cancel()
      return

    $scope.delete = ($event) ->
      $event?.stopPropagation()
      replies = $scope.thread.children?.length or 0

      # We can delete the annotation if it hasn't got any replies or it is
      # private. Otherwise, we ask for a redaction message.
      if replies == 0 or $scope.form.privacy.$viewValue is 'Private'
        # If we're deleting it without asking for a message, confirm first.
        if confirm "Are you sure you want to delete this annotation?"
          if $scope.form.privacy.$viewValue is 'Private' and replies
            #Cascade delete its children
            for reply in $scope.thread.flattenChildren()
              if plugins?.Permissions?.authorize 'delete', reply
                annotator.deleteAnnotation reply

          annotator.deleteAnnotation $scope.model
      else
        $scope.action = 'delete'
        $scope.editing = true
        $scope.origText = $scope.model.text
        $scope.origTags = $scope.model.tags
        $scope.model.text = ''
        $scope.model.tags = ''

    $scope.$watch 'editing', -> $scope.$emit 'toggleEditing'

    $scope.$watch 'model.id', (id) ->
      if id?
        $scope.thread = $scope.model.thread

        # Check if this is a brand new annotation
        if drafts.contains $scope.model
          $scope.editing = true

        $scope.shared_link = "#{baseURI}a/#{$scope.model.id}"

    $scope.$watch 'model.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false

    $scope.$watch 'shared', (newValue) ->
      if newValue? is true
        $timeout -> $element.find('input').focus()
        $timeout -> $element.find('input').select()
        $scope.shared = false
        return

    $scope.$watchCollection 'model.thread.children', (newValue=[]) ->
      return unless $scope.model
      replies = (r.message for r in newValue)
      replies = replies.sort(annotator.sortAnnotations).reverse()
      $scope.model.reply_list = replies

    $scope.toggle = ->
      $element.find('.share-dialog').slideToggle()
      return

    $scope.share = ($event) ->
      $event.stopPropagation()
      return if $element.find('.share-dialog').is ":visible"
      $scope.shared = not $scope.shared
      $scope.toggle()
      return

    $scope.rebuildHighlightText = ->
      if annotator.text_regexp?
        $scope.model.highlightText = $scope.model.text
        for regexp in annotator.text_regexp
          $scope.model.highlightText =
            $scope.model.highlightText.replace regexp, annotator.highlighter


class Editor
  this.$inject = [
    '$location', '$routeParams', '$sce', '$scope',
    'annotator'
  ]
  constructor: (
     $location,   $routeParams,   $sce,   $scope,
     annotator
  ) ->
    {providers} = annotator

    save = ->
      $location.path('/viewer').search('id', $scope.annotation.id).replace()
      for p in providers
        p.channel.notify method: 'onEditorSubmit'
        p.channel.notify method: 'onEditorHide'

    cancel = ->
      $location.path('/viewer').search('id', null).replace()
      for p in providers
        p.channel.notify method: 'onEditorHide'

    $scope.action = if $routeParams.action? then $routeParams.action else 'create'
    if $scope.action is 'create'
      annotator.subscribe 'annotationCreated', save
      annotator.subscribe 'annotationDeleted', cancel
    else
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.subscribe 'annotationUpdated', save

    $scope.$on '$destroy', ->
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.unsubscribe 'annotationUpdated', save
      else
        if $scope.action is 'create'
          annotator.unsubscribe 'annotationCreated', save
          annotator.unsubscribe 'annotationDeleted', cancel

    $scope.annotation = annotator.ongoing_edit

    delete annotator.ongoing_edit

    $scope.$watch 'annotation.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false


class Viewer
  this.$inject = [
    '$location', '$rootScope', '$routeParams', '$scope',
    'annotator'
  ]
  constructor: (
    $location, $rootScope, $routeParams, $scope,
    annotator
  ) ->
    if $routeParams.q
      return $location.path('/page_search').replace()

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

    $scope.openDetails = (annotation) ->
      for p in providers
        p.channel.notify
          method: 'scrollTo'
          params: annotation.$$tag


class Search
  this.$inject = ['$filter', '$location', '$rootScope', '$routeParams', '$sce', '$scope',
                  'annotator', 'viewFilter']
  constructor: ($filter, $location, $rootScope, $routeParams, $sce, $scope,
                annotator, viewFilter) ->
    unless $routeParams.q
      return $location.path('/viewer').replace()

    {providers, threading} = annotator

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

    $scope.openDetails = (annotation) ->
      # Temporary workaround, until search result annotation card
      # scopes get their 'annotation' fields, too.
      return unless annotation

      for p in providers
        p.channel.notify
          method: 'scrollTo'
          params: annotation.$$tag

    $scope.$watchCollection 'annotations', (nVal, oVal) =>
      refresh()

    refresh = =>
      query = $routeParams.q
      [$scope.matches, $scope.filters] = viewFilter.filter $rootScope.annotations, query
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
        unless root_annotation in $rootScope.annotations then continue

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

      $rootScope.search_annotations = threads
      $scope.threads = threads
      for thread in threads
        $rootScope.focus thread.message, true

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


class Notification
  this.inject = ['$scope']
  constructor: (
    $scope
  ) ->


angular.module('h.controllers', imports)
.controller('AppController', App)
.controller('AnnotationController', Annotation)
.controller('EditorController', Editor)
.controller('ViewerController', Viewer)
.controller('SearchController', Search)
.controller('NotificationController', Notification)
