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


# Dummy class that wraps annotator until the Auth plugin is removed.
class AngularAnnotator extends Annotator
  this.$inject = ['$document']
  constructor: ($document) ->
    super(document.createElement('div'))


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
  # Returns the matched annotation IDs list,
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
.service('annotator', AngularAnnotator)
.service('viewFilter', ViewFilter)
