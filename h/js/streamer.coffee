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

  this.$inject = ['$location', '$scope']
  constructor: ($location, $scope) ->
    $scope.streaming = false
    $scope.annotations = []
    $scope.bads = []

    @parser = new ClauseParser()

    #Json structure we will watch and update
    $scope.filter =
      match_policy :  'include_any'
      clauses : []
      actions :
        create: true
        edit: true
        delete: true
      past_data:
        load_past: 'hits'
        go_back: 5
        hits: 100

    #parse for route params
    params = $location.search()
    if params.match_policy in @strategies
      $scope.filter.match_policy = params.match_policy

    if params.action_create
       if (typeof params.action_create) is 'boolean'
         $scope.filter.actions.create = params.action_create
       else
         $scope.filter.actions.create = params.action_create is 'true'
    if params.action_edit
       if (typeof params.action_edit) is 'boolean'
         $scope.filter.actions.edit = params.action_edit
       else
         $scope.filter.actions.edit = params.action_edit is 'true'
    if params.action_delete
       if (typeof params.action_delete) is 'boolean'
         $scope.filter.actions.delete = params.action_delete
       else
         $scope.filter.actions.delete = params.action_delete is 'true'

    if params.load_past in @past_modes
      $scope.filter.past_data.load_past = params.load_past
    if params.hits? and parseInt(params.hits) is not NaN
      $scope.filter.past_data.hits = parseInt(params.hits)
    if params.go_back? and parseInt(params.go_back) is not NaN
      $scope.filter.past_data.go_back = parseInt(params.go_back)

    if params.clauses
      test_clauses = params.clauses.replace ",", " "
      res = @parser.parse_clauses test_clauses
      if res[1]?.length is 0
        $scope.filter.clauses = res[0]
        $scope.clauses = test_clauses
    else
      $scope.clauses = ""

    console.log $scope.filter

    $scope.toggle_past = ->
      switch $scope.filter.past_data.load_past
        when 'none' then $scope.filter.past_data.load_past = 'time'
        when 'time' then $scope.filter.past_data.load_past = 'hits'
        when 'hits' then $scope.filter.past_data.load_past = 'none'

    $scope.$watch 'filter', (newValue, oldValue) =>
      json = JSON.stringify $scope.filter, undefined, 2
      $scope.json_content = syntaxHighlight json
    ,true

    $scope.clause_change = =>
      if $scope.clauses.slice(-1) is ' ' or $scope.clauses.length is 0
        res = @parser.parse_clauses($scope.clauses)
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

      res = @parser.parse_clauses($scope.clauses)
      if res
        $scope.filter.clauses = res[0]
        $scope.bads = res[1]
      unless $scope.bads.length is 0
        return

      transports = ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__', transports)

      $scope.sock.onopen = ->
        $scope.sock.send (JSON.stringify $scope.filter)
        $scope.$apply =>
          $scope.streaming = true

      $scope.sock.onclose = ->
        $scope.$apply =>
          $scope.streaming = false

      $scope.sock.onmessage = (msg) =>
        $scope.$apply =>
          data = msg.data[0]
          unless data instanceof Array then data = [data]
          action = msg.data[1]
          for annotation in data
            annotation['action'] = action
            annotation['quote'] = get_quote annotation
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

angular.module('h.streamer',['h.filters','bootstrap'])
  .controller('StreamerCtrl', Streamer)


