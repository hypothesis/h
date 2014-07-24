imports = [
  'h.filters',
  'h.searchfilters'
]


class Hypothesis extends Annotator
  events:
    'annotationCreated': 'updateAncestors'
    'annotationUpdated': 'updateAncestors'
    'annotationDeleted': 'updateAncestors'

  # Plugin configuration
  options:
    noDocAccess: true
    Discovery: {}
    Permissions:
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
  ]
  constructor: (
     $document,   $location,   $rootScope,   $route,   $window,
  ) ->
    super ($document.find 'body')

    window.annotator = this

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
      'uri', 'diffCaseOnly', 'document', '_updatedAnnotation'
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
            if source is $window.parent then @host = channel
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
    $rootScope.focused = []

    $rootScope.focus = (annotation,
      announceToDoc = false,
      announceToCards = false
    ) =>
      unless annotation
        console.log "Warning: trying to focus on null annotation"
        return

      return if annotation in $rootScope.focused

      # Put this on the list
      $rootScope.focused.push annotation
      # Tell the document, if we have to
      this._broadcastFocusInfo() if announceToDoc
      # Tell to the annotation cards, if we have to
      this._scheduleFocusUpdate() if announceToCards

    $rootScope.unFocus = (annotation,
      announceToDoc = false,
      announceToCards = false
    ) =>
      index = $rootScope.focused.indexOf annotation
      return if index is -1

      # Remove from the list
      $rootScope.focused.splice index, 1
      # Tell the document, if we have to
      this._broadcastFocusInfo() if announceToDoc
      # Tell to the annotation cards, if we have to
      this._scheduleFocusUpdate() if announceToCards

    # Add new annotations to the view when they are created
    this.subscribe 'annotationCreated', (a) =>
      unless a.references?
        $rootScope.annotations.unshift a

    # Remove annotations from the application when they are deleted
    this.subscribe 'annotationDeleted', (a) =>
      $rootScope.annotations = $rootScope.annotations.filter (b) -> b isnt a
      $rootScope.search_annotations = $rootScope.search_annotations.filter (b) -> b.message?

  _broadcastFocusInfo: ->
    $rootScope = @element.injector().get '$rootScope'
    for p in @providers
      p.channel.notify
        method: 'setFocusedHighlights'
        params: (a.$$tag for a in $rootScope.focused)

  # Schedule the broadcasting of the focusChanged signal
  # to annotation cards
  _scheduleFocusUpdate: ->
    return if @_focusUpdatePending
    @_focusUpdatePending = true
    $timeout = @element.injector().get('$timeout')
    $rootScope = @element.injector().get('$rootScope')
    $timeout (=>
      # Announce focus changes
      $rootScope.$broadcast 'focusChange'
      delete @_focusUpdatePending
    ), 100

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

    .bind('showViewer', (ctx, {view, ids, focused}) =>
      ids ?= []
      return unless this.discardDrafts()
      $rootScope.$apply =>
        this.showViewer view, this._getAnnotationsFromIDs(ids), focused
    )

    .bind('updateViewer', (ctx, {view, ids, focused}) =>
      ids ?= []
      $rootScope.$apply =>
        this.updateViewer view, this._getAnnotationsFromIDs(ids), focused
    )

    .bind('toggleViewerSelection', (ctx, {ids, focused}) =>
      $rootScope.$apply =>
        this.toggleViewerSelection this._getAnnotationsFromIDs(ids), focused
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
      @host?.notify
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

  # Just some debug output
  loadAnnotations: (annotations) ->
    console.log "Loaded", annotations.length, "annotations."
    super

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

  toggleViewerSelection: (annotations=[], focused) =>
    annotations = annotations.filter (a) -> a?
    @element.injector().invoke [
      '$rootScope',
      ($rootScope) =>
        if $rootScope.viewState.view is "Selection"
          # We are already in selection mode; just XOR this list
          # to the current selection
          @buildReplyList annotations
          list = $rootScope.annotations
          for a in annotations
            index = list.indexOf a
            if index isnt -1
              list.splice index, 1
              $rootScope.unFocus a, true, true
            else
              list.push a
              if focused
                $rootScope.focus a, true, true
        else
          # We are not in selection mode,
          # so we switch to it, and make this list
          # the new selection
          $rootScope.viewState.view = "Selection"
          $rootScope.annotations = annotations
    ]
    this

  updateViewer: (viewName, annotations=[], focused = false) =>
    annotations = annotations.filter (a) -> a?
    @element.injector().invoke [
      '$rootScope',
      ($rootScope) =>
        @buildReplyList annotations

        # Do we have to replace the focused list with this?
        if focused
          # Nuke the old focus list
          $rootScope.focused = []
          # Add the new elements
          for a in annotations
            $rootScope.focus a, true, true
        else
          # Go over the old list, and unfocus the ones
          # that are not on this list
          for a in $rootScope.focused.slice() when a not in annotations
            $rootScope.unFocus a, true, true

        # Update the main annotations list
        $rootScope.annotations = annotations

        unless $rootScope.viewState.view is viewName
          # We are changing the view
          $rootScope.viewState.view = viewName
          $rootScope.showViewSort true, true
    ]
    this

  showViewer: (viewName, annotations=[], focused = false) =>
    this.show()
    @element.injector().invoke [
      '$location',
      ($location) =>
        $location.path('/viewer').replace()
    ]
    this.updateViewer viewName, annotations, focused

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
      '$location', '$rootScope', 'drafts'
      ($location,   $rootScope,   drafts) =>
        @ongoing_edit = annotation

        unless this.plugins.Auth? and this.plugins.Auth.haveValidToken()
          $rootScope.$apply ->
            $rootScope.$broadcast 'showAuth', true
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

      entities = {}

      for p in @annotator.providers
        for uri in p.entities
          unless entities[uri]?
            console.log "Loading annotations for: " + uri
            entities[uri] = true
            this.loadAnnotationsFromSearch (angular.extend {}, query, uri: uri)

      this.entities = Object.keys(entities)

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
        if @plugins.Permissions?.user
          console.log "Social View filter: single player mode."
          query.user = @plugins.Permissions.user
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

  setTool: (name) =>
    return if name is @tool
    return unless this.discardDrafts()

    if name is 'highlight'
      # Check login state first
      unless @plugins.Permissions?.user
        scope = @element.scope()
        # If we are not logged in, start the auth process
        scope.ongoingHighlightSwitch = true
        scope.sheet.collapsed = false
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

  # Is this annotation a reply?
  isReply: (annotation) ->
    # The presence of references means that this is a reply
    annotation.references?.length

  # Discard all drafts, deleting unsaved annotations from the annotator
  discardDrafts: ->
    return @element.injector().get('drafts').discard()


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


class ViewFilter
  checkers:
    quote:
      autofalse: (annotation) -> return annotation.references?
      value: (annotation) ->
        for target in annotation.target
          return target.quote if target.quote?
        ''
      match: (term, value) -> return value.indexOf(term) > -1
    since:
      autofalse: (annotation) -> return not annotation.updated?
      value: (annotation) -> return annotation.updated
      match: (term, value) ->
        delta = Math.round((+new Date - new Date(value)) / 1000)
        return delta <= term
    tag:
      autofalse: (annotation) -> return not annotation.tags?
      value: (annotation) -> return annotation.tags
      match: (term, value) -> return value in term
    text:
      autofalse: (annotation) -> return not annotation.text?
      value: (annotation) -> return annotation.text
      match: (term, value) -> return value.indexOf(term) > -1
    uri:
      autofalse: (annotation) -> return not annotation.uri?
      value: (annotation) -> return annotation.uri
      match: (term, value) -> return value is term
    user:
      autofalse: (annotation) -> return not annotation.user?
      value: (annotation) ->
        # XXX: Hopefully there is a cleaner solution
        # XXX: To reach persona filter from here
        return (annotation.user?.match /^acct:([^@]+)@(.+)/)?[1]
      match: (term, value) -> return value is term
    any:
      fields: ['quote', 'text', 'tag', 'user']



  this.$inject = ['$filter', 'searchfilter']
  constructor: ($filter, searchfilter) ->
    @user_filter = $filter('persona')
    @searchfilter = searchfilter

  _matches: (filter, value, match) ->
    matches = true

    for term in filter.terms
      unless match term, value
        matches = false
        if filter.operator is 'and'
          break
      else
        matches = true
        if filter.operator is 'or'
          break
    matches

  _arrayMatches: (filter, value, match) ->
    matches = true
    # Make copy for filtering
    copy = value.slice()
    copy.filter (e) ->
      not match filter.terms, e

    if (filter.operator is 'and' and copy.length < value.length) or
    (filter.operator is 'or' and not copy.length)
        matches = false
    matches

  _anyMatches: (filter, value, match) ->
    matchresult = []
    for term in filter.terms
      if angular.isArray value
          matchresult.push match value, term
      else
          matchresult.push match term, value
    matchresult

  _checkMatch: (filter, annotation, checker) ->
    autofalsefn = checker.autofalse
    return false if autofalsefn? and autofalsefn annotation

    value = checker.value annotation
    if angular.isArray value
      if filter.lowercase then value = value.map (e) -> e.toLowerCase()
      return @_arrayMatches filter, value, checker.match
    else
      value = value.toLowerCase() if filter.lowercase
      return @_matches filter, value, checker.match


  # Filters a set of annotations, according to a given query.
  #
  # annotations is the input list of annotations (array)
  # ToDo: update me I'm not up to date!
  # query is the query; it's a map. Supported key values are:
  #   user: username to search for
  #   text: text to search for in the body (all the words must be present)
  #   quote: text to search for in the quote (exact phrase must be present)
  #   tags: list of tags to search for. (all must be present)
  #   time: maximum age of annotation. Accepted values:
  #     '5 min', '30 min', '1 hour', '12 hours',
  #     '1 day', '1 week', '1 month', '1 year'
  #
  # All search is case insensitive.
  #
  # Returns the list of matching annotation IDs.
  filter: (annotations, query) =>
    filters = @searchfilter.generateFacetedFilter query.query
    results = []

    # Check for given limit
    # Find the minimal
    limit = 0
    if filters.result.terms.length
      limit = filter.result.terms[0]
      for term in filter.result.terms
        if limit > term then limit = term

    # Convert terms to lowercase if needed
    for _, filter of filters
      if filter.lowercase then filter.terms.map (e) -> e.toLowerCase()

    # Now that this filter is called with the top level annotations, we have to add the children too
    annotationsWithChildren = []
    for annotation in annotations
      annotationsWithChildren.push annotation
      children = annotation.thread?.flattenChildren()
      if children?.length > 0
        for child in children
          annotationsWithChildren.push child

    for annotation in annotationsWithChildren
      matches = true
      #ToDo: What about given zero limit?
      # Limit reached
      if limit and results.length >= limit then break

      for category, filter of filters
        break unless matches
        terms = filter.terms
        # No condition for this category
        continue unless terms.length

        switch category
          when 'result'
            # Handled above
            continue
          when 'any'
            # Special case
            matchterms = []
            matchterms.push false for term in terms

            for field in @checkers.any.fields
              conf = @checkers[field]

              continue if conf.autofalse? and conf.autofalse annotation
              value = conf.value annotation
              if angular.isArray value
                if filter.lowercase
                  value = value.map (e) -> e.toLowerCase()
              else
                value = value.toLowerCase() if filter.lowercase
              matchresult = @_anyMatches filter, value, conf.match
              matchterms = matchterms.map (t, i) -> t or matchresult[i]

            # Now let's see what we got.
            matched = 0
            for _, value of matchterms
              matched++ if value

            if (filter.operator is 'or' and matched  > 0) or (filter.operator is 'and' and matched is terms.length)
              matches = true
            else
              matches  = false
          else
            # For all other categories
            matches = @_checkMatch filter, annotation, @checkers[category]
      if matches
        results.push annotation.id

    [results, filters]


angular.module('h.services', imports)
.provider('drafts', DraftProvider)
.service('annotator', Hypothesis)
.service('viewFilter', ViewFilter)
