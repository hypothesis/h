#ToDo: write me
# This class will parse the search filter and produce a faceted search filter object
class SearchFilter

  # This function will slice the searchtext
  # Slice character: space,
  # but an expression between quotes (' or ") is considered one
  _tokenize: (searchtext) ->
    return [] unless searchtext
    tokens = searchtext.match /(?:[^\s"']+|"[^"]*"|'[^']*')+/g

    # Cut the opening and closing quote characters
    for token in tokens
      start = token.slice 0,1
      end = token.slice -1
      if (start is '"' or start is "'") and (start is end)
        token = token.slice 1, token.length - 1

    tokens

  generateFacetedFilter: (searchtext) ->
    return unless searchtext
    terms = @_tokenize(searchtext)

    any = []
    quote = []
    result = []
    since = []
    tag = []
    text = []
    uri = []
    user = []

    for term in terms
      filter = term.slice 0, term.indexOf ":"
      unless filter? then filter = ""
      switch filter
        when 'quote' then quote.push term[6..]
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
        when 'tag' then tag.push term[4..]
        when 'text' then text.push term[5..]
        when 'uri' then uri.push term[4..]
        when 'user' then user.push term[5..]
        else any.push term
    any:
      terms: any
      operator: 'and'
      lowercase: true
    quote:
      terms: quote
      operator: 'lower'
      lowercase: true
    result:
      terms: result
      operator: 'min'
      lowercase: false
    since:
      terms: since
      operator: 'min'
      lowercase: false
    tag:
      terms: tag
      operator: 'and'
      lowercase: true
    text:
      terms: text
      operator: 'and'
      lowercase: true
    uri:
      terms: uri
      operator: 'or'
      lowercase: true
    user:
      terms: user
      operator: 'or'
      lowercase: true


# This class will process the results of search and generate the correct filter
# It expects the following dict format as rules
# { facet_name : {
#      formatter: to format the value (optional)
#      path: json path mapping to the annotation field
#      exact_match: true|false (default: true)
#      case_sensitive: true|false (default: false)
#      and_or: and|or for multiple values should it threat them as 'or' or 'and' (def: or)
#      operator: if given it'll use this operator regardless of other circumstances
#
#      options: backend specific options
#      options.es: elasticsearch specific options
#      options.es.query_type : can be: simple, query_string, match
#         defaults to: simple, determines which es query type to use
#      options.es.cutoff_frequency: if set, the query will be given a cutoff_frequency for this facet
#      options.es.and_or: match queries can use this, defaults to and
# }
# The models is the direct output from visualsearch
class QueryParser
  rules:
    user:
      formatter: (user) ->
        'acct:' + user + '@' + window.location.hostname
      path: '/user'
      exact_match: true
      case_sensitive: false
      and_or: 'or'
    text:
      path: '/text'
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    tags:
      path: '/tags'
      exact_match: false
      case_sensitive: false
      and_or: 'or'
    quote:
      path: "/quote"
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    uri:
      formatter: (uri) ->
        uri.toLowerCase()
      path: '/uri'
      exact_match: false
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
      exact_match: false
      case_sensitive: true
      and_or: 'and'
      operator: 'ge'

  parseModels: (models) ->
    # Cluster facets together
    categories = {}
    for searchItem in models
      category = searchItem.attributes.category
      value = searchItem.attributes.value
      if category of categories
        categories[category].push value
      else
        categories[category] = [value]
    categories

  populateFilter: (filter, query) =>
    # Populate a filter with a query object
    for category, values of query
      unless @rules[category]? then continue
      unless values.length then continue
      rule = @rules[category]

      unless angular.isArray values
        values = [values]

      # Now generate the clause with the help of the rule
      exact_match = if rule.exact_match? then rule.exact_match else true
      case_sensitive = if rule.case_sensitive? then rule.case_sensitive else false
      and_or = if rule.and_or? then rule.and_or else 'or'
      mapped_field = if rule.path? then rule.path else '/'+category

      if and_or is 'or'
        val_list = ''
        first = true
        for val in values
          unless first then val_list += ',' else first = false
          value_part = if rule.formatter then rule.formatter val else val
          val_list += value_part
        oper_part =
          if rule.operator? then rule.operator
          else if exact_match then 'one_of' else 'match_of'
        filter.addClause mapped_field, oper_part, val_list, case_sensitive, rule.options
      else
        oper_part =
          if rule.operator? then rule.operator
          else if exact_match then 'equals' else 'matches'
        for val in values
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


angular.module('h.searchfilters', [])
.service('searchfilter', SearchFilter)
.service('queryparser', QueryParser)
.service('streamfilter', StreamFilter)
