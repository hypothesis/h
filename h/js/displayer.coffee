get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(This is a reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class Displayer
  path: window.location.protocol + '//' + window.location.hostname + ':' +
    window.location.port + '/__streamer__'
  idTable : {}

  this.$inject = ['$scope','$element','$timeout','streamfilter']
  constructor: ($scope, $element, $timeout, streamfilter) ->
    $scope.root = document.init_annotation
    $scope.annotation = $scope.root.annotation
    $scope.annotations = [$scope.annotation]
    $scope.annotation.replies = []
    $scope.annotation.reply_count = 0
    @idTable[$scope.annotation.id] = $scope.annotation
    $scope.filter =
      streamfilter
        .setPastDataNone()
        .setMatchPolicyIncludeAny()
        .addClausesParse('references:^' + $scope.annotation.id)
        .addClausesParse('id:=' + $scope.annotation.id)
        .getFilter()

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
      $scope.sock = new SockJS @path

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

    $scope.get_quote_classes = =>
      'yui3-u-1' + if ($scope.annotation.text or $scope.annotation.replies.length) then ' t-yui3-u-1-2' else ''

    if $scope.annotation.referrers?
      $scope.manage_new_data $scope.annotation.referrers, 'past'

    document.init_annotation = null
    $scope.open()

angular.module('h.displayer',['h.streamfilter','h.filters','bootstrap'])
  .controller('DisplayerCtrl', Displayer)
