get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(This is a reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class Displayer
  this.$inject = ['$scope','$element','$timeout']

  constructor: ($scope, $element, $timeout) ->
    $scope.replies = []
    $scope.reply_count = 0
    $scope.id = document.body.attributes.internalid.value
    $scope.filter =
      match_policy :  'include_all'
      clauses : [
        field: "/references"
        operator: "first_of"
        value: $scope.id
        ]
      actions :
        create: true
        edit: true
        delete: true
      past_data:
        load_past: 'replies'
        id_for_reply: $scope.id

    console.log $scope.filter
    $scope.open = ->
      transports = ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__', transports)

      $scope.sock.onopen = ->
        $scope.sock.send JSON.stringify $scope.filter

      $scope.sock.onclose = ->
        $timeout $scope.open, 5000

      $scope.sock.onmessage = (msg) =>
        console.log 'Got something'
        console.log msg
        $scope.$apply =>
          data = msg.data[0]
          unless data instanceof Array then data = [data]
          action = msg.data[1]
          for annotation in data
            annotation.quote = get_quote annotation
            switch action
              when 'create', 'past'
                $scope.reply_count += 1
                #Find the thread for the reply
                replies = $scope.replies
                list = replies
                for reference in annotation.references
                    for reply in replies
                      if reply.id is reference
                        list = reply
                        reply.reply_count += 1
                        replies = reply.replies
                        break

                #Find the place to insert annotation
                pos = 0
                for reply in replies
                  if reply.updated < annotation.updated
                    break
                  pos += 1
                annotation.replies = []
                annotation.reply_count = 0
                replies.splice pos, 0, annotation

              when 'edit'
                console.log 'edit'
              when 'delete'
                console.log 'delete'
          console.log $scope.replies


    $scope.open()

angular.module('h.displayer',['h.filters','bootstrap'])
  .controller('DisplayerCtrl', Displayer)
