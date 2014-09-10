# The render function accepts a scope and a data object and schedule the scope
# to be updated with the provided data and digested before the next repaint
# using window.requestAnimationFrame() (or a fallback). If the resulting digest
# causes a subsequent invocation of the render function the digest rate is
# effectively limited to ensure a responsive user interface.
renderFactory = ['$$rAF', ($$rAF) ->
  renderFrame = null
  renderQueue = []

  render = ->
    return renderFrame = null if renderQueue.length is 0
    {data, cb} = renderQueue.shift()
    $$rAF(render)
    cb(data)

  (data, cb) ->
    renderQueue.push {data, cb}
    renderFrame = $$rAF(render) unless renderFrame
]


class Hypothesis extends Annotator
  events:
    'annotationCreated': 'digest'
    'annotationDeleted': 'digest'
    'annotationUpdated': 'digest'
    'annotationsLoaded': 'digest'

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

  this.$inject = ['$document', '$window']
  constructor:   ( $document,   $window ) ->
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
      'uri', 'diffCaseOnly', 'document',
    ]
    this.addPlugin 'Bridge',
      gateway: true
      formatter: (annotation) =>
        formatted = {}
        for k, v of annotation when k in whitelist
          formatted[k] = v
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

  _setupXDM: (options) ->
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
      @element.scope().$apply =>
        return if @element.scope().ongoingEdit
        this.hide()
    )

    .bind('open', =>
      # Pop out the sidebar
      @element.scope().$apply => this.show()
    )

    .bind('showViewer', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.showViewer this._getLocalAnnotations(tags)
    )

    .bind('updateViewer', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.updateViewer this._getLocalAnnotations(tags)
    )

    .bind('toggleViewerSelection', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.toggleViewerSelection this._getLocalAnnotations(tags)
    )

    .bind('setTool', (ctx, name) =>
      @element.scope().$apply => this.setTool name
    )

    .bind('setVisibleHighlights', (ctx, state) =>
      @element.scope().$apply => this.setVisibleHighlights state
    )

   # Look up an annotation based on its bridge tag
  _getLocalAnnotation: (tag) -> @plugins.Bridge.cache[tag]

   # Look up a list of annotations, based on their bridge tags
  _getLocalAnnotations: (tags) -> this._getLocalAnnotation t for t in tags

  _setupWrapper: ->
    @wrapper = @element.find('#wrapper')
    this

  _setupDocumentEvents: ->
    document.addEventListener 'dragover', (event) =>
      @host?.notify
        method: 'dragFrame'
        params: event.screenX
    this

  # Override things not used in the angular version.
  _setupDynamicStyle: -> this
  _setupViewer: -> this
  _setupEditor: -> this

  # Override things not needed, because we don't access the document
  # with this instance
  _setupDocumentAccessStrategies: -> this
  _scan: -> this

  # Do nothing in the app frame, let the host handle it.
  setupAnnotation: (annotation) ->
    annotation.highlights = []
    annotation

  toggleViewerSelection: (annotations=[]) ->
    scope = @element.scope()

    selected = scope.selectedAnnotations or {}
    for a in annotations
      if selected[a.id]
        delete selected[a.id]
      else
        selected[a.id] = true

    count = Object.keys(selected).length
    scope.selectedAnnotationsCount = count

    if count
      scope.selectedAnnotations = selected
    else
      scope.selectedAnnotations = null

    this

  updateViewer: (annotations=[]) ->
    # TODO: re-implement
    this

  showViewer: (annotations=[]) ->
    scope = @element.scope()
    selected = {}
    for a in annotations
      selected[a.id] = true
    scope.selectedAnnotations = selected
    scope.selectedAnnotationsCount = Object.keys(selected).length
    this.show()
    this

  showEditor: (annotation) ->
    scope = @element.scope()
    scope.ongoingEdit = mail.messageContainer(annotation)
    scope.$digest()  # XXX: unify with other RPC, digest cycle
    delete scope.selectedAnnotations
    this.show()
    this

  show: ->
    @element.scope().frame.visible = true

  hide: ->
    @element.scope().frame.visible = false

  digest: ->
    @element.scope().$evalAsync angular.noop

  patch_store: ->
    scope = @element.scope()
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
      # Update the annotation with the new data
      annotation = angular.extend annotation, data

      # Update the thread table
      update = (parent) ->
        for child in parent.children when child.message is annotation
          scope.threading.idTable[data.id] = child
          return true
        return false

      # Check its references
      references = annotation.references or []
      if typeof(annotation.references) == 'string' then references = []
      for ref in references.slice().reverse()
        container = scope.threading.idTable[ref]
        continue unless container?
        break if update container

      # Check the root
      update scope.threading.root

      # Sync data to other frames
      @plugins.Bridge.sync([annotation])

      # Tell angular about the changes.
      scope.$digest()

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

  setTool: (name) ->
    return if name is @tool
    return unless @element.injector().get('drafts').discard()

    if name is 'highlight'
      # Check login state first
      unless @plugins.Permissions?.user
        scope = @element.scope()
        # If we are not logged in, start the auth process
        scope.ongoingHighlightSwitch = true
        @element.injector().get('identity').request()
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

  setVisibleHighlights: (state) ->
    return if state is @visibleHighlights
    @visibleHighlights = state
    this.publish 'setVisibleHighlights', state
    for p in @providers
      p.channel.notify
        method: 'setVisibleHighlights'
        params: state


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
  # This object is the filter matching configuration used by the filter() function
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

    copy = copy.filter (e) ->
      match filter.terms, e

    if (filter.operator is 'and' and copy.length < filter.terms.length) or
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
      if typeof(value[0]) == 'string'
        value = value.map (v) -> v.toLowerCase()
      return @_arrayMatches filter, value, checker.match
    else
      value = value.toLowerCase() if typeof(value) == 'string'
      return @_matches filter, value, checker.match

  # Filters a set of annotations, according to a given query.
  # Inputs:
  #   annotations is the input list of annotations (array)
  #   filters is the query is a faceted filter generated by SearchFilter
  #
  # It'll handle the annotation matching by the returned facet configuration (operator, lowercase, etc.)
  # and the here configured @checkers. This @checkers object contains instructions how to verify the match.
  # Structure:
  # [facet_name]:
  #   autofalse: a function for a preliminary false match result
  #              (i.e. if the annotation does not even have a 'text' field, do not try to match the 'text' facet)
  #   value: a function to extract to facet value for the annotation.
  #         (i.e. for the quote facet it is the annotation.target.quote from the right target from the annotations)
  #   match: a function to check if the extracted value matches with the facet value
  #         (i.e. for the text facet it has to check that if the facet is a substring of the annotation.text or not.
  #
  # Returns a two-element list:
  # [
  #   matched annotation IDs list,
  #   the faceted filters
  # ]
  filter: (annotations, filters) ->
    limit = Math.min((filters.result?.terms or [])...)
    count = 0

    results = for annotation in annotations
      break if count >= limit

      match = true
      for category, filter of filters
        break unless match
        continue unless filter.terms.length

        switch category
          when 'any'
            categoryMatch = false
            for field in @checkers.any.fields
              if @_checkMatch(filter, annotation, @checkers[field])
                categoryMatch = true
                break
            match = categoryMatch
          else
            match = @_checkMatch filter, annotation, @checkers[category]

      continue unless match
      count++
      annotation.id

angular.module('h.services', [])
.factory('render', renderFactory)
.provider('drafts', DraftProvider)
.service('annotator', Hypothesis)
.service('viewFilter', ViewFilter)
