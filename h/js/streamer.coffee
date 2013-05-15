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
  this.$inject = ['$scope']

  constructor: ($scope) ->
    $scope.sidebar_json = false

    $scope.streaming = false
    $scope.annotations = []

    $scope.matchPolicy = 'exclude_any'
    $scope.action =
      'create': true
      'edit': true
      'delete': true

    $scope.past_list = ['none', 'time', 'hits']
    $scope.past =
      load_past: 2
      go_back: 5
      hits: 100

    $scope.filter_fields = ['thread', 'text', 'user','uri']
    $scope.operators = ['=', '>', '<', '=>', '>=', '<=', '=<', '[', '#']
    $scope.operator_mapping =
      '=': 'equals'
      '>': 'gt'
      '<': 'lt'
      '=>' : 'ge'
      '<=' : 'ge'
      '=<': 'le'
      '<=' : 'le'
      '[' : 'one_of'
      '#' : 'matches'

    $scope.start_streaming = ->
      if $scope.streaming
        $scope.sock.close
        $scope.streaming = false

      $scope.json_content = syntaxHighlight $scope.generate_json()
      transports = ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__', transports)

      $scope.sock.onopen = ->
        $scope.sock.send $scope.generate_json()
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

    $scope.stop_streaming = ->
      $scope.sock.close
      $scope.streaming = false

    $scope.parse_clauses = ->
      bads = []
      structure = []
      unless $scope.clauses
        return
      clauses = $scope.clauses.split ' '
      for clause in clauses
        #Here comes the long and boring validation checking
        clause = clause.trim()
        if clause.length < 1 then continue

        parts = clause.split /:(.+)/
        unless parts.length > 1
          bads.push [clause, 'Filter clause is not well separated']
          continue

        unless parts[0] in $scope.filter_fields
          bads.push [clause, 'Unknown filter field']
          continue

        field = parts[0]
        operator_found = false
        for operator in $scope.operators
          if (parts[1].indexOf operator) is 0
            oper = $scope.operator_mapping[operator]
            if operator is '['
              value = parts[1][operator.length..].split ','
            else
              value = parts[1][operator.length..]
            operator_found = true
            break

        unless operator_found
          bads.push [clause, 'Unknown operator']
          continue

        structure.push
          'field'   : '/' + field
          'operator': oper
          'value'   : value

      structure

    $scope.show_sidebar_json = ->
      $scope.json_content = syntaxHighlight $scope.generate_json()
      $scope.sidebar_json = true

    $scope.generate_json = ->
      clauses = $scope.parse_clauses()
      unless clauses
      	clauses = []
      load = $scope.past['load_past']
      past = { 'load_past': $scope.past_list[load]}
      if load is 1 then past['go_back'] = $scope.past['go_back']
      if load is 2 then past['hits'] = $scope.past['hits']

      struct =
        'match_policy' : $scope.matchPolicy
        'clauses' : clauses
        'actions' : $scope.action
        'past_data': past

      JSON.stringify struct, undefined, 2


angular.module('h.streamer',['h.filters','bootstrap'])
  .controller('StreamerCtrl', Streamer)


