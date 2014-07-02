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

  addClause: (clause) ->
    @filter.clauses.push clause
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


angular.module('h.streamfilter',['bootstrap'])
  .service('streamfilter', StreamFilter)