get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(This is a reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector' 
            quote = selector['exact'] + ' '

  quote

  
angular.module('h.streamer',['h.filters'])
  .controller('StreamerCtrl',
  ($scope, $element) ->
    $scope.streaming = false
    $scope.matchPolicy = 'include_all'
    $scope.annotations = []    
    $scope.action_create = true
    $scope.action_edit = true
    $scope.action_delete = true

    $scope.start_streaming = ->
      if $scope.streaming
        $scope.sock.close
        $scope.streaming = false
               
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + port + '/streamer')    
      $scope.sock.onopen = ->
        $scope.sock.send $scope.generate_json()
        $scope.$apply =>
          $scope.streaming = true
      $scope.sock.onclose = ->
        $scope.$apply =>
          $scope.streaming = false
      $scope.sock.onmessage = (msg) =>
        $scope.$apply =>
          annotation = msg.data[0]
          action = msg.data[1]
          annotation['action'] = action
          annotation['quote'] = get_quote annotation
          $scope.annotations.splice 0,0,annotation
          #window.scrollTo 0, document.body.scrollHeight
          
    $scope.stop_streaming = ->
      $scope.sock.close
      $scope.streaming = false
      
    $scope.filter_fields = ['thread', 'text', 'user']
    $scope.operators = ['=', '>', '<', '=>', '>=', '<=', '=<', '[', '#']
    $scope.operator_mapping = {
      '=': 'equals', '>': 'gt', '<': 'lt', '=>' : 'ge', '<=' : 'ge',
      '=<': 'le', '<=' : 'le', '[' : 'one_of', '#' : 'matches'  
    }  
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
        
        parts = clause.split ':'
        unless parts.length is 2
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

        structure.push {
          'field'   : '/' + field ,
          'operator': oper ,
          'value'   : value
        }
      console.log structure
      console.log bads
      structure
     
    $scope.generate_json = ->
      clauses = $scope.parse_clauses()
      unless clauses
      	clauses = []
      struct = {
        'match_policy' : $scope.matchPolicy,
        'clauses' : clauses,
        'actions' : {
          'create' : $scope.action_create,
          'edit'   : $scope.action_edit,
          'delete' : $scope.action_delete
        }
      }
      JSON.stringify struct
  )


