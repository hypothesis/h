class Hypothesis extends Annotator
  events:
    'annotationCreated': 'updateAncestors'
    'annotationUpdated': 'updateAncestors'
    'annotationDeleted': 'updateAncestors'
    'serviceDiscovery': 'serviceDiscovery'

  # Plugin configuration
  options:
    noDocAccess: true
    Discovery: {}
    Permissions:
      permissions:
        read: ['group:__world__']
      userAuthorize: (action, annotation, user) ->
        if annotation.permissions
          tokens = annotation.permissions[action] || []

          if tokens.length == 0
            # Empty or missing tokens array: only admin can perform action.
            return false

          for token in tokens
            if this.userId(user) == token
              return true
            if token == 'group:__world__'
              return true
            if token == 'group:__authenticated__' and this.user?
              return true

          # No tokens matched: action should not be performed.
          return false

        # Coarse-grained authorization
        else if annotation.user
          return user and this.userId(user) == this.userId(annotation.user)

        # No authorization info on annotation: free-for-all!
        true
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')
    Threading: {}

  # Internal state
  providers: null
  host: null

  tool: 'comment'
  visibleHighlights: false

  # Here as a noop just to make the Permissions plugin happy
  # XXX: Change me when Annotator stops assuming things about viewers
  viewer:
    addField: (-> )

  this.$inject = [
    '$document', '$location', '$rootScope', '$route', '$window',
    'authentication', 'drafts'
  ]
  constructor: (
     $document,   $location,   $rootScope,   $route,   $window,
     authentication,   drafts
  ) ->
    Gettext.prototype.parse_locale_data annotator_locale_data
    super ($document.find 'body')

    window.annotator = this

    # Generate client ID
    buffer = new Array(16)
    uuid.v4 null, buffer, 0
    @clientID = uuid.unparse buffer
    $.ajaxSetup headers: "x-client-id": @clientID

    @auth = authentication
    @providers = []
    @socialView =
      name: "none" # "single-player"

    this.patch_store()

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    whitelist = [
      'diffHTML', 'inject', 'quote', 'ranges', 'target', 'id', 'references',
      'uri', 'diffCaseOnly', '_updatedAnnotation'
    ]
    this.addPlugin 'Bridge',
      gateway: true
      formatter: (annotation) =>
        formatted = {}
        for k, v of annotation when k in whitelist
          formatted[k] = v
        if annotation.thread? and annotation.thread?.children.length
          formatted.reply_count = annotation.thread.flattenChildren().length
        else
          formatted.reply_count = 0
        formatted
      parser: (annotation) =>
        parsed = {}
        for k, v of annotation when k in whitelist
          parsed[k] = v
        parsed
      onConnect: (source, origin, scope) =>
        options =
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: =>
            console.log "Provider functions are ready for #{origin}"
            if source is @element.injector().get('$window').parent
              @host = channel
        entities = []
        channel = this._setupXDM options

        channel.call
          method: 'getDocumentInfo'
          success: (info) =>
            entityUris = {}
            entityUris[info.uri] = true
            for link in info.metadata.link
              entityUris[link.href] = true if link.href
            for href of entityUris
              entities.push href
            this.plugins.Store?.loadAnnotations()

        channel.notify
          method: 'setTool'
          params: this.tool

        channel.notify
          method: 'setVisibleHighlights'
          params: this.visibleHighlights

        @providers.push
          channel: channel
          entities: entities

    # Add some info to new annotations
    this.subscribe 'beforeAnnotationCreated', (annotation) =>
      # Annotator assumes a valid array of targets and highlights.
      unless annotation.target?
        annotation.target = []
      unless annotation.highlights?
        annotation.highlights = []

      # Register it with the draft service, except when it's an injection
       # This is an injection. Delete the marker.
      if annotation.inject
        # Set permissions for private
        permissions = @plugins.Permissions
        userId = permissions.options.userId permissions.user
        annotation.permissions =
          read: [userId]
          admin: [userId]
          update: [userId]
          delete: [userId]

    # Set default owner permissions on all annotations
    for event in ['beforeAnnotationCreated', 'beforeAnnotationUpdated']
      this.subscribe event, (annotation) =>
        permissions = @plugins.Permissions
        if permissions.user?
          userId = permissions.options.userId(permissions.user)
          for action, roles of annotation.permissions
            unless userId in roles then roles.push userId

    # Track the visible annotations in the root scope
    $rootScope.annotations = []
    $rootScope.search_annotations = []

    # Add new annotations to the view when they are created
    this.subscribe 'annotationCreated', (a) =>
      unless a.references?
        $rootScope.annotations.unshift a

    # Remove annotations from the application when they are deleted
    this.subscribe 'annotationDeleted', (a) =>
      $rootScope.annotations = $rootScope.annotations.filter (b) -> b isnt a
      $rootScope.search_annotations = $rootScope.search_annotations.filter (b) -> b.message?

  _setupXDM: (options) ->
    $rootScope = @element.injector().get '$rootScope'

    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    provider = Channel.build options
        # Dodge toolbars [DISABLE]
        #@provider.getMaxBottom (max) =>
        #  @element.css('margin-top', "#{max}px")
        #  @element.find('.topbar').css("top", "#{max}px")
        #  @element.find('#gutter').css("margin-top", "#{max}px")
        #  @plugins.Heatmap.BUCKET_THRESHOLD_PAD += max

    provider

    .bind('publish', (ctx, args...) => this.publish args...)

    .bind('back', =>
      # Navigate "back" out of the interface.
      $rootScope.$apply =>
        return unless this.discardDrafts()
        this.hide()
    )

    .bind('open', =>
      # Pop out the sidebar
      $rootScope.$apply => this.show()
    )

    .bind('showViewer', (ctx, ids=[]) =>
      return unless this.discardDrafts()
      this.showViewer this._getAnnotationsFromIDs ids
    )

    .bind('updateViewer', (ctx, ids=[]) =>
      this.updateViewer this._getAnnotationsFromIDs ids
    )

    .bind('setTool', (ctx, name) =>
      $rootScope.$apply => this.setTool name
    )

    .bind('setVisibleHighlights', (ctx, state) =>
      $rootScope.$apply => this.setVisibleHighlights state
    )

    .bind('addEmphasis', (ctx, ids=[]) =>
      this.addEmphasis this._getAnnotationsFromIDs ids
    )

    .bind('removeEmphasis', (ctx, ids=[]) =>
      this.removeEmphasis this._getAnnotationsFromIDs ids
    )

   # Look up an annotation based on the ID
  _getAnnotationFromID: (id) -> @threading.getContainer(id)?.message

   # Look up a list of annotations, based on their IDs
  _getAnnotationsFromIDs: (ids) -> this._getAnnotationFromID id for id in ids

  _setupWrapper: ->
    @wrapper = @element.find('#wrapper')
    .on 'mousewheel', (event, delta) ->
      # prevent overscroll from scrolling host frame
      # This is actually a bit tricky. Starting from the event target and
      # working up the DOM tree, find an element which is scrollable
      # and has a scrollHeight larger than its clientHeight.
      # I've obsered that some styles, such as :before content, may increase
      # scrollHeight of non-scrollable elements, and that there a mysterious
      # discrepancy of 1px sometimes occurs that invalidates the equation
      # typically cited for determining when scrolling has reached bottom:
      #   (scrollHeight - scrollTop == clientHeight)
      $current = $(event.target)
      while $current.css('overflow') in ['hidden', 'visible']
        $parent = $current.parent()
        # Break out on document nodes
        if $parent.get(0).nodeType == 9
          event.preventDefault()
          return
        $current = $parent
      scrollTop = $current[0].scrollTop
      scrollEnd = $current[0].scrollHeight - $current[0].clientHeight
      if delta > 0 and scrollTop == 0
        event.preventDefault()
      else if delta < 0 and scrollEnd - scrollTop <= 5
        event.preventDefault()
    this

  _setupDocumentEvents: ->
    document.addEventListener 'dragover', (event) =>
      for p in @providers
        p.channel.notify
          method: 'dragFrame'
          params: event.screenX

  # Override things not used in the angular version.
  _setupDynamicStyle: -> this
  _setupViewer: -> this
  _setupEditor: -> this

  # Override things not needed, because we don't access the document
  # with this instance
  _setupDocumentAccessStrategies: -> this
  _scan: -> this

  # (Optionally) put some HTML formatting around a quote
  getHtmlQuote: (quote) -> quote

  # Do nothing in the app frame, let the host handle it.
  setupAnnotation: (annotation) ->
    annotation.highlights = []
    annotation

  sortAnnotations: (a, b) ->
    a_upd = if a.updated? then new Date(a.updated) else new Date()
    b_upd = if b.updated? then new Date(b.updated) else new Date()
    a_upd.getTime() - b_upd.getTime()

  buildReplyList: (annotations=[]) =>
    $filter = @element.injector().get '$filter'
    for annotation in annotations
      if annotation?
        thread = @threading.getContainer annotation.id
        children = (r.message for r in (thread.children or []))
        annotation.reply_list = children.sort(@sortAnnotations).reverse()
        @buildReplyList children

  updateViewer: (annotations=[]) =>
    annotations = annotations.filter (a) -> a?
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) =>
        @buildReplyList annotations
        $rootScope.annotations = annotations
        $rootScope.$digest()
    ]
    this

  showViewer: (annotations=[]) =>
    annotations = annotations.filter (a) -> a?
    this.show()
    @element.injector().invoke [
      '$location', '$rootScope',
      ($location, $rootScope) =>
        @buildReplyList annotations
        $rootScope.annotations = annotations
        $location.path('/viewer').replace()
        $rootScope.$digest()
    ]
    this

  addEmphasis: (annotations=[]) =>
    annotations = annotations.filter (a) -> a? # Filter out null annotations
    for a in annotations
      a.$emphasis = true
    @element.injector().get('$rootScope').$digest()

  removeEmphasis: (annotations=[]) =>
    annotations = annotations.filter (a) -> a? # Filter out null annotations
    for a in annotations
      delete a.$emphasis
    @element.injector().get('$rootScope').$digest()

  clickAdder: =>
    for p in @providers
      p.channel.notify
        method: 'adderClick'

  showEditor: (annotation) =>
    this.show()
    @element.injector().invoke [
      '$location', '$rootScope', '$route', 'drafts'
      ($location, $rootScope, $route, drafts) =>
        @ongoing_edit = annotation

        unless this.plugins.Auth? and this.plugins.Auth.haveValidToken()
          $route.current.locals.$scope.$apply ->
            $route.current.locals.$scope.$emit 'showAuth', true
          for p in @providers
            p.channel.notify method: 'onEditorHide'
          return

        # Set the path
        search =
          id: annotation.id
          action: 'create'
        $location.path('/editor').search(search)

        # Store the draft
        drafts.add annotation

        # Digest the change
        $rootScope.$digest()
    ]
    this

  show: =>
    @element.scope().frame.visible = true

  hide: =>
    @element.scope().frame.visible = false

  isOpen: =>
    @element.scope().frame.visible

  patch_store: ->
    $location = @element.injector().get '$location'
    $rootScope = @element.injector().get '$rootScope'

    Store = Annotator.Plugin.Store

    # When the Store plugin is first instantiated, don't load annotations.
    # They will be loaded manually as entities are registered by participating
    # frames.
    Store.prototype.loadAnnotations = ->
      query = limit: 1000
      @annotator.considerSocialView.call @annotator, query

      this.entities ?= {}
      for p in @annotator.providers
        for uri in p.entities
          unless this.entities[uri]?
            console.log "Loading annotations for: " + uri
            this.entities[uri] = true
            this.loadAnnotationsFromSearch (angular.extend query, uri: uri)

    # When the store plugin finishes a request, update the annotation
    # using a monkey-patched update function which updates the threading
    # if the annotation has a newly-assigned id and ensures that the id
    # is enumerable.
    Store.prototype.updateAnnotation = (annotation, data) =>
      unless Object.keys(data).length
        return

      if annotation.id? and annotation.id != data.id
        # Update the id table for the threading
        thread = @threading.getContainer annotation.id
        thread.id = data.id
        @threading.idTable[data.id] = thread
        delete @threading.idTable[annotation.id]

        # The id is no longer temporary and should be serialized
        # on future Store requests.
        Object.defineProperty annotation, 'id',
          configurable: true
          enumerable: true
          writable: true

        # If the annotation is loaded in a view, switch the view
        # to reference the new id.
        search = $location.search()
        if search? and search.id == annotation.id
          search.id = data.id
          $location.search(search).replace()

      # Update the annotation with the new data
      annotation = angular.extend annotation, data
      @plugins.Bridge?.updateAnnotation annotation

      # Give angular a chance to react
      $rootScope.$digest()

  considerSocialView: (query) ->
    switch @socialView.name
      when "none"
        # Sweet, nothing to do, just clean up previous filters
        console.log "Not applying any Social View filters."
        delete query.user
      when "single-player"
        if (p = @auth.persona)?
          console.log "Social View filter: single player mode."
          query.user = "acct:" + p.username + "@" + p.provider
        else
          console.log "Social View: single-player mode, but ignoring it, since not logged in."
          delete query.user
      else
        console.warn "Unsupported Social View: '" + @socialView.name + "'!"

  # Bubbles updates through the thread so that guests see accurate
  # reply counts.
  updateAncestors: (annotation) =>
    for ref in (annotation.references?.slice().reverse() or [])
      rel = (@threading.getContainer ref).message
      if rel?
        $timeout = @element.injector().get('$timeout')
        $timeout (=> @plugins.Bridge.updateAnnotation rel), 10
        this.updateAncestors(rel)
        break  # Only the nearest existing ancestor, the rest is by induction.

  serviceDiscovery: (options) =>
    @options.Store ?= {}
    angular.extend @options.Store, options
    this.addPlugin 'Store', @options.Store

  setTool: (name) =>
    return if name is @tool
    return unless this.discardDrafts()

    if name is 'highlight'
      # Check login state first
      unless @plugins.Auth? and @plugins.Auth.haveValidToken()
        scope = @element.scope()
        # If we are not logged in, start the auth process
        scope.ongoingHighlightSwitch = true
        # No need to reload annotations upon login, since Social View change
        # will trigger a reload anyway.
        scope.skipAuthChangeReload = true
        scope.sheet.collapsed = false
        scope.sheet.tab = 'login'
        this.show()
        return

      this.socialView.name = 'single-player'
    else
      this.socialView.name = 'none'

    @tool = name
    this.publish 'setTool', name
    for p in @providers
      p.channel.notify
        method: 'setTool'
        params: name

  setVisibleHighlights: (state) =>
    return if state is @visibleHighlights
    @visibleHighlights = state
    this.publish 'setVisibleHighlights', state
    for p in @providers
      p.channel.notify
        method: 'setVisibleHighlights'
        params: state

  # Is this annotation a comment?
  isComment: (annotation) ->
    # No targets and no references means that this is a comment
    not (annotation.references?.length or annotation.target?.length)


  # Discard all drafts, deleting unsaved annotations from the annotator
  discardDrafts: ->
    return @element.injector().get('drafts').discard()

class AuthenticationProvider
  constructor: ->
    @actions =
      load:
        method: 'GET'
        withCredentials: true

    for action in ['login', 'logout', 'register', 'forgot', 'activate']
      @actions[action] =
        method: 'POST'
        params:
          '__formid__': action
        withCredentials: true

    @actions['claim'] = @actions['forgot']

  $get: [
    '$document', '$resource',
    ($document,   $resource) ->
      baseUrl = $document[0].baseURI.replace(/:(\d+)/, '\\:$1')

      # Strip an empty hash and end in exactly one slash
      baseUrl = baseUrl.replace /#$/, ''
      baseUrl = baseUrl.replace /\/*$/, '/'

      $resource(baseUrl, {}, @actions).load()]


class DraftProvider
  drafts: null

  constructor: ->
    this.drafts = []

  $get: -> this

  add: (draft, cb) -> @drafts.push {draft, cb}

  remove: (draft) ->
    remove = []
    for d, i in @drafts
      remove.push i if d.draft is draft
    while remove.length
      @drafts.splice(remove.pop(), 1)

  contains: (draft) ->
    for d in @drafts
      if d.draft is draft then return true
    return false

  isEmpty: -> @drafts.length is 0

  discard: ->
    text =
      switch @drafts.length
        when 0 then null
        when 1
          """You have an unsaved reply.

          Do you really want to discard this draft?"""
        else
          """You have #{@drafts.length} unsaved replies.

          Do you really want to discard these drafts?"""

    if @drafts.length is 0 or confirm text
      discarded = @drafts.slice()
      @drafts = []
      d.cb?() for d in discarded
      true
    else
      false

angular.module('h.services', ['ngResource','h.filters'])
  .provider('authentication', AuthenticationProvider)
  .provider('drafts', DraftProvider)
  .service('annotator', Hypothesis)
