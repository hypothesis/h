get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class UserStream
  this.$inject = ['$scope','$timeout']
  constructor: ($scope, $timeout) ->
    $scope.annotations = []
    $scope.username = document.body.attributes.internalid.value
    $scope.filter =
      match_policy :  'include_any'
      clauses : [
          field: "/user"
          operator: "equals"
          value: $scope.username
      ]
      actions :
        create: true
        edit: true
        delete: true
      past_data:
        load_past: "hits"
        hits: 100

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation['action'] = action
        annotation['quote'] = get_quote annotation
        $scope.annotations.splice 0,0,annotation

    $scope.open = =>
      $scope.sock = new SockJSWrapper $scope, $scope.filter
      , null
      , $scope.manage_new_data
      ,=>
        $timeout $scope.open, 5000

    $scope.open()


angular.module('h.userstream',['h.filters','bootstrap'])
  .controller('UserStreamCtrl', UserStream)
