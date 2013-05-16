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


class ClauseParser
  this.filter_fields = ['thread', 'text', 'user','uri']
  this.operators = ['=', '>', '<', '=>', '>=', '<=', '=<', '[', '#']
  this.operator_mapping =
    '=': 'equals'
    '>': 'gt'
    '<': 'lt'
    '=>' : 'ge'
    '<=' : 'ge'
    '=<': 'le'
    '<=' : 'le'
    '[' : 'one_of'
    '#' : 'matches'

  this.parse_clauses = (clauses) ->
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
          break

      unless operator_found
        bads.push [clause, 'Unknown operator']
        continue

      structure.push
        'field'   : '/' + field
        'operator': oper
        'value'   : value
    [structure, bads]



class Streamer
  this.$inject = ['$scope']
  this.parser = ClauseParser

  constructor: ($scope) ->
    $scope.streaming = false
    $scope.annotations = []
    $scope.bads = []

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

    $scope.toggle_past = ->
      switch $scope.filter.past_data.load_past
        when 'none' then $scope.filter.past_data.load_past = 'time'
        when 'time' then $scope.filter.past_data.load_past = 'hits'
        when 'hits' then $scope.filter.past_data.load_past = 'none'

    $scope.$watch 'filter', (newValue, oldValue) =>
      json = JSON.stringify $scope.filter, undefined, 2
      $scope.json_content = syntaxHighlight json
    ,true

    $scope.clause_change = ->
      if $scope.clauses.slice(-1) is ' ' or $scope.clauses.length is 0
        res = Streamer.parser.parse_clauses($scope.clauses)
        if res?
          $scope.filter.clauses = res[0]
          $scope.bads = res[1]
        else
          $scope.filter.clauses = []
          $scope.bads = []

    $scope.start_streaming = ->
      if $scope.streaming
        $scope.sock.close()
        $scope.streaming = false

      res = @parser.parse_clauses($scope.clauses)
      $scope.filter.clauses = res[0]
      $scope.bads = res[1]
      unless $scope.bads.length is 0
        return

      transports = ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__', transports)

      $scope.sock.onopen = ->
        $scope.sock.send $scope.filter
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
      $scope.sock.close()
      $scope.streaming = false

angular.module('h.streamer',['h.filters','bootstrap'])
  .controller('StreamerCtrl', Streamer)


