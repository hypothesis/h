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

    $scope.start_streaming = ->
      sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + port + '/streamer')    
      sock.onopen = ->
        $scope.$apply =>
          $scope.streaming = true
      sock.onclose = ->
        $scope.$apply =>
          $scope.streaming = false
      sock.onmessage = (msg) =>
        $scope.$apply =>
          console.log msg.data
          annotation = msg.data[0]
          action = msg.data[1]
          annotation['action'] = action
          annotation['quote'] = get_quote annotation
          $scope.annotations.push annotation
          window.scrollTo 0, document.body.scrollHeight
  )


