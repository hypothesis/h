get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class TagStream
  path: window.location.protocol + '//' + window.location.hostname + ':' +
    window.location.port + '/__streamer__'

  this.$inject = ['$location','$scope','$timeout','streamfilter']
  constructor: ($location, $scope, $timeout, streamfilter) ->
    $scope.annotations = []
    $scope.tag = $location.absUrl().split('/').pop()
    $scope.tagLabel = decodeURIComponent $scope.tag
    $scope.filter =
      streamfilter
        .setPastDataHits(100)
        .setMatchPolicyIncludeAny()
        .setClausesParse('tags:#' + $scope.tag)
        .getFilter()

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        annotation._anim = 'fade'
        $scope.annotations.splice 0,0,annotation

    $scope.open = =>
      $scope.sock = new SockJS(@path)

      $scope.sock.onopen = =>
        $scope.sock.send JSON.stringify $scope.filter

      $scope.sock.onclose = =>
        $timeout $scope.open, 5000

      $scope.sock.onmessage = (msg) =>
        console.log 'Got something'
        console.log msg
        data = msg.data[0]
        action = msg.data[1]
        unless data instanceof Array then data = [data]

        $scope.$apply =>
          $scope.manage_new_data data, action

    $scope.open()


angular.module('h.tagstream',['h.streamfilter', 'h.filters','h.directives','bootstrap'])
  .controller('TagStreamCtrl', TagStream)
