class window.ClauseParser
  filter_fields : ['references', 'text', 'user','uri', 'id']
  operators: ['=', '>', '<', '=>', '>=', '<=', '=<', '[', '#', '^']
  operator_mapping:
    '=': 'equals'
    '>': 'gt'
    '<': 'lt'
    '=>' : 'ge'
    '<=' : 'ge'
    '=<': 'le'
    '<=' : 'le'
    '[' : 'one_of'
    '#' : 'matches'
    '^' : 'first_of'

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
      operator_found = false
      for operator in @operators
        if (parts[1].indexOf operator) is 0
          oper = @operator_mapping[operator]
          if operator is '['
            value = parts[1][operator.length..].split ','
          else
            value = parts[1][operator.length..]
          operator_found = true
          if field is 'user'
            value = 'acct:' + value + '@' + window.location.hostname + ':' + window.location.port
          break

      unless operator_found
        bads.push [clause, 'Unknown operator']
        continue

      structure.push
        'field'   : '/' + field
        'operator': oper
        'value'   : value
    [structure, bads]


class window.StreamerFilter
  strategies: ['include_any', 'include_all', 'exclude_any', 'exclude_all']
  past_modes: ['none','hits','time']

  filter:
      match_policy :  'include_any'
      clauses : []
      actions :
        create: true
        edit: true
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
  getActionEdit: -> return @filter.actions.edit
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

  setActionEdit: (action) ->
    @filter.actions.edit = action
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

  addClause: (field, operator, value) ->
    @filter.clauses.push
      field: field
      operator: operator
      value: value
    this

  setClausesParse: (clauses_to_parse, error_checking = false) ->
    res = @parser.parse_clauses clauses_to_parse
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
    @setActionEdit(true)
    @setActionDelete(true)
    @setPastDataNone()
    @noClauses()
    this
