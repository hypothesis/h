class ClauseParser
  filter_fields : ['references', 'text', 'user','uri', 'id', 'tags']
  operators: ['=', '>', '<', '=>', '>=', '<=', '=<', '[', '#', '^']
  operator_mapping:
    '=': 'equals'
    '>': 'gt'
    '<': 'lt'
    '=>' : 'ge'
    '>=' : 'ge'
    '=<': 'le'
    '<=' : 'le'
    '[' : 'one_of'
    '#' : 'matches'
    '^' : 'first_of'
  insensitive_operator : 'i'

  parse_clauses: (clauses) ->
    bads = []
    structure = []
    unless clauses
      return
    clauses = clauses.split ' '
    for clause in clauses
      #Here comes the long and boring validation checking
      clause = clause.trim()
      if clause.length < 1 then continue

      parts = clause.split /:(.+)/
      unless parts.length > 1
        bads.push [clause, 'Filter clause is not well separated']
        continue

      unless parts[0] in @filter_fields
        bads.push [clause, 'Unknown filter field']
        continue

      field = parts[0]

      if parts[1][0] is @insensitive_operator
        sensitive = false
        rest = parts[1][1..]
      else
        sensitive = true
        rest = parts[1]

      operator_found = false
      for operator in @operators
        if (rest.indexOf operator) is 0
          oper = @operator_mapping[operator]
          if operator is '['
            value = rest[operator.length..].split ','
          else
            value = rest[operator.length..]
          operator_found = true
          if field is 'user'
            value = 'acct:' + value + '@' + window.location.hostname
          break

      unless operator_found
        bads.push [clause, 'Unknown operator']
        continue

      structure.push
        'field'   : '/' + field
        'operator': oper
        'value'   : value
        'case_sensitive': sensitive
    [structure, bads]


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
    @parser = new ClauseParser()

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

  addClause: (clause) ->
    @filter.clauses.push clause
    this

  addClause: (field, operator, value, case_sensitive = false) ->
    @filter.clauses.push
      field: field
      operator: operator
      value: value
      case_sensitive: case_sensitive
    this

  setClausesParse: (clauses_to_parse, error_checking = false) ->
    res = @parser.parse_clauses clauses_to_parse
    if res[1].length
      console.log "Errors while parsing clause:"
      console.log res[1]
    if res? and (not error_checking) or (error_checking and res[1]?.length is 0)
      @filter.clauses = res[0]
    this

  addClausesParse: (clauses_to_parse, error_checking = false) ->
    res = @parser.parse_clauses clauses_to_parse
    if res? and (not error_checking) or (error_checking and res[1]?.length is 0)
      for clause in res[0]
        @filter.clauses.push clause
    this

  resetFilter: ->
    @setMatchPolicyIncludeAny()
    @setActionCreate(true)
    @setActionUpdate(true)
    @setActionDelete(true)
    @setPastDataNone()
    @noClauses()
    this


angular.module('h.streamfilter',['bootstrap'])
  .service('clauseparser', ClauseParser)
  .service('streamfilter', StreamFilter)