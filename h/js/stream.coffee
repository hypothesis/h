get_quote = (annotation) ->
  if annotation.quote? then return annotation.quote
  if not 'target' in annotation then return ''

  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '
  quote

class Stream
  path: window.location.protocol + '//' + window.location.hostname + ':' +
    window.location.port + '/__streamer__'

  this.$inject = ['$location','$scope','$timeout','streamfilter']
  constructor: ($location, $scope, $timeout, streamfilter) ->
    $scope.annotations = []
    urlParts = $location.absUrl().split('/')
    $scope.filterValue = urlParts.pop()
    filterType = urlParts.pop()
    if filterType == "t"
      $scope.filterDescription = "Annotations with tag '#{ $scope.filterValue }'"
      filterClause = 'tags:#' + $scope.filterValue
    else
      $scope.filterDescription = "Annotations by user '#{ $scope.filterValue }'"
      filterClause = 'user:=' + $scope.filterValue
    
    $scope.filter =
      streamfilter
        .setPastDataHits(150)
        .setMatchPolicyIncludeAny()
        .setClausesParse(filterClause)
        .getFilter()

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        annotation._share_link = window.location.protocol +
        '//' + window.location.hostname + ':' + window.location.port + "/a/" + annotation.id
        annotation._anim = 'fade'
        switch action
          when 'create', 'past'
            unless annotation in $scope.annotations
              $scope.annotations.unshift annotation
          when 'update'
            index = 0
            for ann in $scope.annotations
              if ann.id is annotation.id
                #Remove the original
                $scope.annotations.splice index,1
                #Put back the edited
                $scope.annotations.unshift annotation
                break
              index +=1
          when 'delete'
            for ann in $scope.annotations
              if ann.id is annotation.id
                $scope.annotations.splice index,1
                break
              index +=1

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


angular.module('h.stream',['h.streamfilter', 'h.filters','h.directives','bootstrap'])
  .controller('StreamCtrl', Stream)
