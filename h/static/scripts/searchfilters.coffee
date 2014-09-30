# This class will parse the search filter and produce a faceted search filter object
# It expects a search query string where the search term are separated by space character
# and collects them into the given term arrays
class SearchFilter
  # This function will slice the search-text input
  # Slice character: space,
  # but an expression between quotes (' or ") is considered one
  # I.e from the string: "text user:john 'to be or not to be' it will produce:
  # ["text", "user:john", "to be or not to be"]
  _tokenize: (searchtext) ->
    return [] unless searchtext

    # Small helper function for removing quote characters
    # from the beginning- and end of a string, if the
    # quote characters are the same.
    # I.e.
    #   'foo' -> foo
    #   "bar" -> bar
    #   'foo" -> 'foo"
    #   bar"  -> bar"
    _removeQuoteCharacter = (text) ->
      start = text.slice 0,1
      end = text.slice -1
      if (start is '"' or start is "'") and (start == end)
        text = text.slice 1, text.length - 1
      text

    tokens = searchtext.match /(?:[^\s"']+|"[^"]*"|'[^']*')+/g

    # Cut the opening and closing quote characters
    tokens = tokens.map _removeQuoteCharacter

    # Remove quotes for power search.
    # I.e. 'tag:"foo bar"' -> 'tag:foo bar'
    for token, index in tokens
      filter = token.slice 0, token.indexOf ":"
      unless filter? then filter = ""

      if filter in ['quote', 'result', 'since', 'tag', 'text', 'uri', 'user']
        tokenPart = token[filter.length+1..]
        tokens[index] = filter + ':' + (_removeQuoteCharacter tokenPart)

    tokens

  # This function will generate the facets from the search-text input
  # It'll first tokenize it and then sorts them into facet lists
  # The output will be a dict with the following structure:
  # An object with facet_names as keys.
  # A value for a key:
  # [facet_name]:
  #   [operator]: 'and'|'or'|'min' (for the elements of the facet terms list)
  #   [lowercase]: true|false
  #   [terms]: an array for the matched terms for this facet
  # The facet selection is done by analyzing each token.
  # It generally expects a <facet_name>:<facet_term> structure for a token
  # Where the facet names are: 'quote', 'result', 'since', 'tag', 'text', 'uri', 'user
  # Anything that didn't match go to the 'any' facet
  # For the 'since' facet the the time string is scanned and is converted to seconds
  # So i.e the 'since:7min' token will be converted to 7*60 = 420 for the since facet value
  generateFacetedFilter: (searchtext) ->
    any = []
    quote = []
    result = []
    since = []
    tag = []
    text = []
    uri = []
    user = []

    if searchtext
      terms = @_tokenize(searchtext)
      for term in terms
        filter = term.slice 0, term.indexOf ":"
        unless filter? then filter = ""
        switch filter
          when 'quote' then quote.push term[6..].toLowerCase()
          when 'result' then result.push term[7..]
          when 'since'
            # We'll turn this into seconds
            time = term[6..].toLowerCase()
            if time.match /^\d+$/
              # Only digits, assuming seconds
              since.push time
            if time.match /^\d+sec$/
              # Time given in seconds
              t = /^(\d+)sec$/.exec(time)[1]
              since.push t
            if time.match /^\d+min$/
              # Time given in minutes
              t = /^(\d+)min$/.exec(time)[1]
              since.push t * 60
            if time.match /^\d+hour$/
              # Time given in hours
              t = /^(\d+)hour$/.exec(time)[1]
              since.push t * 60 * 60
            if time.match /^\d+day$/
              # Time given in days
              t = /^(\d+)day$/.exec(time)[1]
              since.push t * 60 * 60 * 24
            if time.match /^\d+week$/
              # Time given in week
              t = /^(\d+)week$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 7
            if time.match /^\d+month$/
              # Time given in month
              t = /^(\d+)month$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 30
            if time.match /^\d+year$/
              # Time given in year
              t = /^(\d+)year$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 365
          when 'tag' then tag.push term[4..].toLowerCase()
          when 'text' then text.push term[5..].toLowerCase()
          when 'uri' then uri.push term[4..].toLowerCase()
          when 'user' then user.push term[5..].toLowerCase()
          else any.push term.toLowerCase()

    any:
      terms: any
      operator: 'and'
    quote:
      terms: quote
      operator: 'and'
    result:
      terms: result
      operator: 'min'
    since:
      terms: since
      operator: 'and'
    tag:
      terms: tag
      operator: 'and'
    text:
      terms: text
      operator: 'and'
    uri:
      terms: uri
      operator: 'or'
    user:
      terms: user
      operator: 'or'


# This class will process the results of search and generate the correct filter
# It expects the following dict format as rules
# { facet_name : {
#      formatter: to format the value (optional)
#      path: json path mapping to the annotation field
#      case_sensitive: true|false (default: false)
#      and_or: and|or for multiple values should it threat them as 'or' or 'and' (def: or)
#      operator: if given it'll use this operator regardless of other circumstances
#
#      options: backend specific options
#      options.es: elasticsearch specific options
#      options.es.query_type : can be: simple, query_string, match, multi_match
#         defaults to: simple, determines which es query type to use
#      options.es.cutoff_frequency: if set, the query will be given a cutoff_frequency for this facet
#      options.es.and_or: match and multi_match queries can use this, defaults to and
#      options.es.match_type: multi_match query type
#      options.es.fields: fields to search for in multi-match query
# }
# The models is the direct output from visualsearch
class QueryParser
  rules:
    user:
      path: '/user'
      case_sensitive: false
      and_or: 'or'
    text:
      path: '/text'
      case_sensitive: false
      and_or: 'and'
    tag:
      path: '/tags'
      case_sensitive: false
      and_or: 'and'
    quote:
      path: '/quote'
      case_sensitive: false
      and_or: 'and'
    uri:
      formatter: (uri) ->
        uri.toLowerCase()
      path: '/uri'
      case_sensitive: false
      and_or: 'or'
      options:
        es:
         query_type: 'match'
         cutoff_frequency: 0.001
         and_or: 'and'
    since:
      formatter: (past) ->
        seconds =
          switch past
            when '5 min' then 5*60
            when '30 min' then 30*60
            when '1 hour' then 60*60
            when '12 hours' then 12*60*60
            when '1 day' then 24*60*60
            when '1 week' then 7*24*60*60
            when '1 month' then 30*24*60*60
            when '1 year' then 365*24*60*60
        new Date(new Date().valueOf() - seconds*1000)
      path: '/created'
      case_sensitive: true
      and_or: 'and'
      operator: 'ge'
    any:
      case_sensitive: false
      and_or: 'and'
      path:   ['/quote', '/tags', '/text', '/uri', '/user']
      options:
        es:
         query_type: 'multi_match'
         match_type: 'cross_fields'
         and_or: 'and'
         fields:   ['quote', 'tag', 'text', 'uri', 'user']

  populateFilter: (filter, query) =>
    # Populate a filter with a query object
    for category, value of query
      unless @rules[category]? then continue
      terms = value.terms
      unless terms.length then continue
      rule = @rules[category] 


      # Now generate the clause with the help of the rule
      case_sensitive = if rule.case_sensitive? then rule.case_sensitive else false
      and_or = if rule.and_or? then rule.and_or else 'or'
      mapped_field = if rule.path? then rule.path else '/'+category

      if and_or is 'or'
        oper_part = if rule.operator? then rule.operator else 'match_of'

        value_part = []
        for term in terms
          t = if rule.formatter then rule.formatter term else term
          value_part.push t

        filter.addClause mapped_field, oper_part, value_part, case_sensitive, rule.options
      else
        oper_part = if rule.operator? then rule.operator else 'matches'
        for val in terms
          value_part = if rule.formatter then rule.formatter val else val
          filter.addClause mapped_field, oper_part, value_part, case_sensitive, rule.options


class StreamFilter
  strategies: ['include_any', 'include_all', 'exclude_any', 'exclude_all']
  past_modes: ['none','hits','time']

  filter:
      match_policy :  'include_any'
      clauses : []
      actions :
        create: true
        update: true
        delete: true
      past_data:
        load_past: "none"

  constructor: ->

  getFilter: -> return @filter
  getPastData: -> return @filter.past_data
  getMatchPolicy: -> return @filter.match_policy
  getClauses: -> return @filter.clauses
  getActions: -> return @filter.actions
  getActionCreate: -> return @filter.actions.create
  getActionUpdate: -> return @filter.actions.update
  getActionDelete: -> return @filter.actions.delete

  setPastDataNone: ->
    @filter.past_data =
      load_past: 'none'
    this

  setPastDataHits: (hits) ->
    @filter.past_data =
      load_past: 'hits'
      hits: hits
    this

  setPastDataTime: (time) ->
    @filter.past_data =
      load_past: 'hits'
      go_back: time
    this

  setMatchPolicy: (policy) ->
    @filter.match_policy = policy
    this

  setMatchPolicyIncludeAny: ->
    @filter.match_policy = 'include_any'
    this

  setMatchPolicyIncludeAll: ->
    @filter.match_policy = 'include_all'
    this

  setMatchPolicyExcludeAny: ->
    @filter.match_policy = 'exclude_any'
    this

  setMatchPolicyExcludeAll: ->
    @filter.match_policy = 'exclude_all'
    this

  setActions: (actions) ->
    @filter.actions = actions
    this

  setActionCreate: (action) ->
    @filter.actions.create = action
    this

  setActionUpdate: (action) ->
    @filter.actions.update = action
    this

  setActionDelete: (action) ->
    @filter.actions.delete = action
    this

  noClauses: ->
    @filter.clauses = []
    this

  addClause: (field, operator, value, case_sensitive = false, options = {}) ->
    @filter.clauses.push
      field: field
      operator: operator
      value: value
      case_sensitive: case_sensitive
      options: options
    this

  resetFilter: ->
    @setMatchPolicyIncludeAny()
    @setActionCreate(true)
    @setActionUpdate(true)
    @setActionDelete(true)
    @setPastDataNone()
    @noClauses()
    this


angular.module('h')
.service('searchfilter', SearchFilter)
.service('queryparser', QueryParser)
.service('streamfilter', StreamFilter)
