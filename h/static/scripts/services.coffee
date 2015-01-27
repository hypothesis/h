###*
# @ngdoc service
# @name render
# @param {function()} fn A function to execute in a future animation frame.
# @returns {function()} A function to cancel the execution.
# @description
# The render service is a wrapper around `window#requestAnimationFrame()` for
# scheduling sequential updates in successive animation frames. It has the
# same signature as the original function, but will queue successive calls
# for future frames so that at most one callback is handled per animation frame.
# Use this service to schedule DOM-intensive digests.
###
renderFactory = ['$$rAF', ($$rAF) ->
  cancel = null
  queue = []

  render = ->
    return cancel = null if queue.length is 0
    do queue.shift()
    $$rAF(render)

  (fn) ->
    queue.push fn
    unless cancel then cancel = $$rAF(render)
    -> queue = (f for f in queue when f isnt fn)
]


class Hypothesis extends Annotator
  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'
    'annotationDeleted': 'annotationDeleted'
    'annotationsLoaded': 'digest'

  # Plugin configuration
  options:
    noDocAccess: true
    Threading: {}

  # Internal state
  providers: null
  host: null

  tool: 'comment'
  visibleHighlights: false

  this.$inject = ['$document', '$window', 'store']
  constructor:   ( $document,   $window,   store ) ->
    super ($document.find 'body')

    @providers = []
    @store = store

    # Load plugins
    for own name, opts of @options
      if not @plugins[name] and name of Annotator.Plugin
        this.addPlugin(name, opts)

    # Set up the bridge plugin, which bridges the main annotation methods
    # between the host page and the panel widget.
    whitelist = ['target', 'document', 'uri']
    this.addPlugin 'Bridge',
      gateway: true
      formatter: (annotation) ->
        formatted = {}
        for k, v of annotation when k in whitelist
          formatted[k] = v
        formatted
      parser: (annotation) ->
        parsed = new store.AnnotationResource()
        for k, v of annotation when k in whitelist
          parsed[k] = v
        parsed
      onConnect: (source, origin, scope) =>
        options =
          window: source
          origin: origin
          scope: "#{scope}:provider"
          onReady: => if source is $window.parent then @host = channel
        channel = this._setupXDM options
        provider = channel: channel, entities: []

        channel.call
          method: 'getDocumentInfo'
          success: (info) =>
            provider.entities = (link.href for link in info.metadata.link)
            @providers.push provider
            @element.scope().$digest()
            this.digest()

        # Allow the host to define it's own state
        unless source is $window.parent
          channel.notify
            method: 'setTool'
            params: this.tool

          channel.notify
            method: 'setVisibleHighlights'
            params: this.visibleHighlights

  _setupXDM: (options) ->
    # jschannel chokes FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options.origin = '*'

    provider = Channel.build options

    .bind('publish', (ctx, args...) => this.publish args...)

    .bind('back', =>
      # Navigate "back" out of the interface.
      @element.scope().$apply => this.hide()
    )

    .bind('open', =>
      # Pop out the sidebar
      @element.scope().$apply => this.show()
    )

    .bind('showEditor', (ctx, tag) =>
      @element.scope().$apply =>
        this.showEditor this._getLocalAnnotation(tag)
    )

    .bind('showAnnotations', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.showViewer this._getLocalAnnotations(tags)
    )

    .bind('updateAnnotations', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.updateViewer this._getLocalAnnotations(tags)
    )

    .bind('focusAnnotations', (ctx, tags=[]) =>
      @element.scope().$apply =>
        this.focusAnnotations tags
    )

    .bind('toggleAnnotationSelection', (ctx, tags=[]) =>
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

  createAnnotation: (annotation) ->
    annotation = new @store.AnnotationResource(annotation)
    this.publish 'beforeAnnotationCreated', annotation
    annotation

  deleteAnnotation: (annotation) ->
    annotation.$delete(id: annotation.id).then =>
      this.publish 'annotationDeleted', annotation
    annotation

  loadAnnotations: (annotations) ->
    annotations = for annotation in annotations
      container = @plugins.Threading.idTable[annotation.id]
      if container?.message
        angular.copy annotation, container.message
        this.publish 'annotationUpdated', container.message
        continue
      else
        annotation
    super (new @store.AnnotationResource(a) for a in annotations)

  # Do nothing in the app frame, let the host handle it.
  setupAnnotation: (annotation) -> annotation

  # Properly set the selectedAnnotations- and the Count variables
  _setSelectedAnnotations: (selected) ->
    scope = @element.scope()
    count = Object.keys(selected).length
    scope.selectedAnnotationsCount = count

    if count
      scope.selectedAnnotations = selected
    else
      scope.selectedAnnotations = null

  toggleViewerSelection: (annotations=[]) ->
    scope = @element.scope()
    scope.search.query = ''

    selected = scope.selectedAnnotations or {}
    for a in annotations
      if selected[a.id]
        delete selected[a.id]
      else
        selected[a.id] = true
    @_setSelectedAnnotations selected
    this

  focusAnnotations: (tags) ->
    @element.scope().focusedAnnotations = tags

  updateViewer: (annotations=[]) ->
    # TODO: re-implement
    this

  showViewer: (annotations=[]) ->
    scope = @element.scope()
    scope.search.query = ''
    selected = {}
    for a in annotations
      selected[a.id] = true
    @_setSelectedAnnotations selected
    this.show()
    this

  showEditor: (annotation) ->
    delete @element.scope().selectedAnnotations
    this.show()
    this

  show: ->
    @host.notify method: 'showFrame'

  hide: ->
    @host.notify method: 'hideFrame'

  digest: ->
    @element.scope().$evalAsync angular.noop

  beforeAnnotationCreated: (annotation) ->
    annotation.user = @element.injector().get('auth').user
    annotation.permissions = {}
    @digest()

  annotationDeleted: (annotation) ->
    scope = @element.scope()
    if scope.selectedAnnotations?[annotation.id]
      delete scope.selectedAnnotations[annotation.id]
      @_setSelectedAnnotations scope.selectedAnnotations

  setTool: (name) ->
    return if name is @tool
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
  _drafts: null

  constructor: ->
    @_drafts = []

  $get: -> this

  all: -> draft for {draft} in @_drafts

  add: (draft, cb) -> @_drafts.push {draft, cb}

  remove: (draft) ->
    remove = []
    for d, i in @_drafts
      remove.push i if d.draft is draft
    while remove.length
      @_drafts.splice(remove.pop(), 1)

  contains: (draft) ->
    for d in @_drafts
      if d.draft is draft then return true
    return false

  isEmpty: -> @_drafts.length is 0

  discard: ->
    text =
      switch @_drafts.length
        when 0 then null
        when 1
          """You have an unsaved reply.

          Do you really want to discard this draft?"""
        else
          """You have #{@_drafts.length} unsaved replies.

          Do you really want to discard these drafts?"""

    if @_drafts.length is 0 or confirm text
      discarded = @_drafts.slice()
      @_drafts = []
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
        quotes = for t in (annotation.target or [])
          for s in (t.selector or []) when s.type is 'TextQuoteSelector'
            unless s.exact then continue
            s.exact
        quotes = Array::concat quotes...
        quotes.join('\n')
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
      match: (term, value) -> return value.indexOf(term) > -1
    user:
      autofalse: (annotation) -> return not annotation.user?
      value: (annotation) -> return annotation.user
      match: (term, value) -> return value.indexOf(term) > -1
    any:
      fields: ['quote', 'text', 'tag', 'user']

  this.$inject = ['stringHelpers']
  constructor: (stringHelpers) ->

    @_normalize = (e) ->
      if typeof e is 'string'
        return stringHelpers.uniFold(e)
      else return e

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
    copy = filter.terms.slice()

    copy = copy.filter (e) ->
      match value, e

    if (filter.operator is 'and' and copy.length < filter.terms.length) or
    (filter.operator is 'or' and not copy.length)
      matches = false
    matches

  _checkMatch: (filter, annotation, checker) ->
    autofalsefn = checker.autofalse
    return false if autofalsefn? and autofalsefn annotation

    value = checker.value annotation
    if angular.isArray value
      value = value.map (e) -> e.toLowerCase()
      value = value.map (e) => @_normalize(e)
      return @_arrayMatches filter, value, checker.match
    else
      value = value.toLowerCase()
      value = @_normalize(value)
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
  #   value: a function to extract to facet value for the annotation.
  #   match: a function to check if the extracted value matches with the facet value
  #
  # Returns a two-element list:
  # [
  #   matched annotation IDs list,
  #   the faceted filters
  # ]
  filter: (annotations, filters) ->
    limit = Math.min((filters.result?.terms or [])...)
    count = 0

    # Normalizing the filters, need to do only once.
    for _, filter of filters
      if filter.terms
        filter.terms = filter.terms.map (e) =>
          e = e.toLowerCase()
          e = @_normalize e
          e

    for annotation in annotations
      break if count >= limit

      match = true
      for category, filter of filters
        break unless match
        continue unless filter.terms.length

        switch category
          when 'any'
            categoryMatch = false
            for field in @checkers.any.fields
              for term in filter.terms
                termFilter = {terms: [term], operator: "and"}
                if @_checkMatch(termFilter, annotation, @checkers[field])
                  categoryMatch = true
                  break
            match = categoryMatch
          else
            match = @_checkMatch filter, annotation, @checkers[category]

      continue unless match
      count++
      annotation.id

angular.module('h')
.factory('render', renderFactory)
.provider('drafts', DraftProvider)
.service('annotator', Hypothesis)
.service('viewFilter', ViewFilter)
