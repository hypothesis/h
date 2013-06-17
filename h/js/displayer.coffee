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
  idTable : {}

  constructor: ($scope, $element, $timeout) ->
    $scope.annotation = {}
    $scope.annotations = [$scope.annotation]
    $scope.annotation.replies = []
    $scope.annotation.reply_count = 0
    $scope.annotation.id = document.body.attributes.internalid.value
    @idTable[$scope.annotation.id] = $scope.annotation
    $scope.filter =
      match_policy :  'include_any'
      clauses : [
          field: "/references"
          operator: "first_of"
          value: $scope.annotation.id
        ,
          field: "/id"
          operator: "equals"
          value: $scope.annotation.id
        ]
      actions :
        create: true
        edit: true
        delete: true
      past_data:
        load_past: "none"

    $scope.change_annotation_content = (id, new_annotation) =>
      to_change = @idTable[id]
      replies = to_change.replies
      reply_count = to_change.reply_count
      for k, v of to_change
        delete to_change.k
      angular.extend to_change, new_annotation
      to_change.replies = replies
      to_change.reply_count = reply_count

    $scope.open = =>
      transports = ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
      $scope.sock = new SockJS(window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__', transports)

      $scope.sock.onopen = ->
        $scope.sock.send JSON.stringify $scope.filter

      $scope.sock.onclose = ->
        $timeout $scope.open, 5000

      $scope.sock.onmessage = (msg) =>
        console.log 'Got something'
        console.log msg
        data = msg.data[0]
        action = msg.data[1]
        unless data instanceof Array then data = [data]
        $scope.$apply =>
          $scope.manage_new_data data, action

    $scope.manage_new_data = (data, action) =>
      #sort annotations by creation date
      data.sort (a, b) ->
        if a.created > b.created then return 1
        if a.created > b.created then return -1
        0

      for annotation in data
        annotation.quote = get_quote annotation
        switch action
          when 'create', 'past'
            #Ignore duplicates caused by server restarting
            if annotation.id in @idTable
              break

            for i in [$scope.annotation.ref_length..annotation.references.length-1]
              reference = annotation.references[i]
              @idTable[reference].reply_count += 1

            replies = @idTable[annotation.references[annotation.references.length-1]].replies

            #Find the place to insert annotation
            pos = 0
            for reply in replies
              if reply.updated < annotation.updated
                break
              pos += 1
            annotation.replies = []
            annotation.reply_count = 0
            @idTable[annotation.id] = annotation
            replies.splice pos, 0, annotation

          when 'edit'
            $scope.change_annotation_content annotation.id, annotation

          when 'delete'
            if 'deleted' in annotation
              #Redaction
              $scope.change_annotation_content annotation.id, annotation
            else
              #Real delete
              unless @idTable[annotation.id]?
                break

              #Update the reply counter for all referenced annotation
              for i in [$scope.annotation.ref_length..annotation.references.length-1]
                reference = annotation.references[i]
                @idTable[reference].reply_count -= 1

              replies = @idTable[annotation.references[annotation.references.length-1]].replies

              #Find the place to insert annotation
              pos = replies.indexOf @idTable[annotation.id]
              replies.splice pos, 1
              delete @idTable[annotation.id]

    if document.initial_replies?
      $scope.manage_new_data document.initial_replies, 'past'
      document.initial_replies = ''
    $scope.open()

angular.module('h.displayer',['h.filters','bootstrap'])
  .controller('DisplayerCtrl', Displayer)
