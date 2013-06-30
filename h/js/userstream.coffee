get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class UserStream

  this.$inject = ['$scope','$timeout','streamfilter']
  constructor: ($scope, $timeout, streamfilter) ->
    $scope.annotations = []
    $scope.username = document.body.attributes.internalid.value
    $scope.filter =
      streamfilter
        .setPastDataHits(100)
        .setMatchPolicyIncludeAny()
        .setClausesParse('user:=' + $scope.username)
        .getFilter()

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        annotation._anim = 'fade'
        $scope.annotations.splice 0,0,annotation

    $scope.open = =>
      $scope.sock = new SockJSWrapper $scope, $scope.filter
      , null
      , $scope.manage_new_data
      ,=>
        $timeout $scope.open, 5000

    $scope.open()


angular.module('h.userstream',['h.streamfilter', 'h.filters','h.directives','bootstrap'])
  .controller('UserStreamCtrl', UserStream)
