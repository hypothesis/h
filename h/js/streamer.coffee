get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(This is a reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector' 
            quote = selector['exact'] + ' '

  quote

syntaxHighlight = (json) ->
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) -> 
    cls = 'number'
    if /^"/.test(match) 
      if /:$/.test(match) then cls = 'key'
      else cls = 'string'
    else 
      if /true|false/.test(match) then cls = 'boolean'
      else 
        if /null/.test(match) then cls = 'null'
    return '<span class="' + cls + '">' + match + '</span>'
  )

class Streamer
  strategies: ['include_any', 'include_all', 'exclude_any', 'exclude_all']
  past_modes: ['none','hits','time']

  this.$inject = ['$location', '$scope', 'streamfilter', 'clauseparser']
  constructor: ($location, $scope, streamfilter, clauseparser) ->
    $scope.streaming = false
    $scope.annotations = []
    $scope.bads = []
    $scope.time = 5
    $scope.hits = 100

    @sfilter = streamfilter
    @sfilter.setPastDataHits(100)
    $scope.filter = @sfilter.filter

    #parse for route params
    params = $location.search()
    if params.match_policy in @strategies
      $scope.filter.match_policy = params.match_policy

    if params.action_create
       if (typeof params.action_create) is 'boolean'
         @sfilter.setActionCreate(params.action_create)
       else
         @sfilter.setActionCreate(params.action_create is 'true')
    if params.action_edit
       if (typeof params.action_edit) is 'boolean'
         @sfilter.setActionEdit(params.action_edit)
       else
         @sfilter.setActionEdit(params.action_edit is 'true')
    if params.action_delete
       if (typeof params.action_delete) is 'boolean'
         @sfilter.setActionDelete(params.action_delete)
       else
         @sfilter.setActionDelete(params.action_delete is 'true')

    if params.load_past in @past_modes
      if params.hits? and parseInt(params.hits) is not NaN
        @sfilter.setPastDataHits(parseInt(params.hits))
      if params.go_back? and parseInt(params.go_back) is not NaN
        @sfilter.setPastDataTime(parseInt(params.go_back))

    if params.clauses
      test_clauses = params.clauses.replace ",", " "
      @sfilter.setClausesParse(test_clauses)
      $scope.clauses = test_clauses
    else
      $scope.clauses = ''

    console.log $scope.filter

    $scope.toggle_past = ->
      switch $scope.filter.past_data.load_past
        when 'none' then @sfilter.setPastDataTime($scope.time)
        when 'time' then @sfilter.setPastDataHits($scope.hits)
        when 'hits' then @sfilter.setPastDataNone()

    $scope.$watch 'filter', (newValue, oldValue) =>
      json = JSON.stringify $scope.filter, undefined, 2
      $scope.json_content = syntaxHighlight json
    ,true

    $scope.clause_change = =>
      if $scope.clauses.slice(-1) is ' ' or $scope.clauses.length is 0
        res = clauseparser.parse_clauses($scope.clauses)
        if res?
          $scope.filter.clauses = res[0]
          $scope.bads = res[1]
        else
          $scope.filter.clauses = []
          $scope.bads = []

    $scope.start_streaming = =>
      if $scope.streaming
        $scope.sock.close()
        $scope.streaming = false

      res = clauseparser.parse_clauses($scope.clauses)
      if res
        $scope.filter.clauses = res[0]
        $scope.bads = res[1]
      unless $scope.bads.length is 0
        return
      $scope.open()

    $scope.open = =>
      $scope.sock = new SockJSWrapper $scope, $scope.filter
      , =>
        $scope.streaming = true
      , $scope.manage_new_data
      ,=>
        $scope.streaming = false

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        $scope.annotations.splice 0,0,annotation

      #Update the parameters
      $location.search
        'match_policy': $scope.filter.match_policy
        'action_create': $scope.filter.actions.create
        'action_edit': $scope.filter.actions.edit
        'action_delete': $scope.filter.actions.delete
        'load_past': $scope.filter.past_data.load_past
        'go_back': $scope.filter.past_data.go_back
        'hits': $scope.filter.past_data.hits
        'clauses' : $scope.clauses.replace " ", ","

    $scope.stop_streaming = ->
      $scope.sock.close()
      $scope.streaming = false

angular.module('h.streamer',['h.streamfilter','h.filters','bootstrap'])
  .controller('StreamerCtrl', Streamer)


