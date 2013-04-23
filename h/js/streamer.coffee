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
    $scope.annotations = []    
    $scope.action_create = true
    $scope.action_update = true
    $scope.action_delete = true

    $scope.start_streaming = ->
      if $scope.streaming
        $scope.sock.close
        $scope.streaming = false
               
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + port + '/streamer')    
      $scope.sock.onopen = ->
        filter = {}
        if $scope.username?.length > 1
          filter.users = $scope.username.split ','
        filter.actions = {
          create : $scope.action_create,
          update : $scope.action_update,
          delete : $scope.action_delete 
        }
        $scope.sock.send JSON.stringify filter
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
          $scope.annotations.push annotation
          window.scrollTo 0, document.body.scrollHeight
  )


