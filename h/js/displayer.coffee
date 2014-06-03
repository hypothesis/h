imports = [
  'bootstrap'
  'h.filters'
  'h.directives'
  'h.helpers'
  'h.streamfilter'
]


get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = '(This is a reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '

  quote

class Displayer
  idTable : {}

  this.$inject = ['$scope','$element','$timeout','baseURI', 'streamfilter']
  constructor: ($scope, $element, $timeout, baseURI, streamfilter) ->
    # Set streamer url
    streamerURI = baseURI.replace /\/\w+(\/?\??[^\/]*)\/?$/, '/__streamer__'

    # Generate client ID
    buffer = new Array(16)
    uuid.v4 null, buffer, 0
    @clientID = uuid.unparse buffer

    $scope.root = document.init_annotation
    $scope.annotation = $scope.root.annotation
    $scope.annotations = [$scope.annotation]
    $scope.annotation.replies = []
    $scope.annotation.reply_count = 0
    $scope.annotation.ref_length =
      if $scope.annotation.references? then $scope.annotation.references.length else 0
    $scope.full_deleted = false
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
      $scope.sock = new SockJS streamerURI

      $scope.sock.onopen = =>
        sockmsg =
          filter: $scope.filter
          clientID: @clientID
        $scope.sock.send JSON.stringify sockmsg

      $scope.sock.onclose = =>
        $timeout $scope.open, 5000

      $scope.sock.onmessage = (msg) =>
        console.log 'Got something'
        console.log msg
        unless msg.data.type? and msg.data.type is 'annotation-notification'
          return
        data = msg.data.payload
        action = msg.data.options.action
        unless data instanceof Array then data = [data]

        $scope.$apply =>
          $scope.manage_new_data data, action

    $scope.manage_new_data = (data, action) =>
      #sort annotations by creation date
      data.sort (a, b) ->
        if a.created > b.created then return 1
        if a.created < b.created then return -1
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

          when 'update'
            $scope.change_annotation_content annotation.id, annotation

          when 'delete'
            if 'deleted' in annotation
              #Redaction
              $scope.change_annotation_content annotation.id, annotation
            else
              #Real delete
              unless @idTable[annotation.id]?
                break

              if $scope.annotation.id is annotation.id
                $scope.full_deleted = true
              else
                #Reply delete
                #Update the reply counter for all referenced annotation
                for i in [$scope.annotation.ref_length..annotation.references.length-1]
                  reference = annotation.references[i]
                  @idTable[reference].reply_count -= 1

                replies = @idTable[annotation.references[annotation.references.length-1]].replies

                #Find the place to insert annotation
                pos = replies.indexOf @idTable[annotation.id]
                replies.splice pos, 1
                delete @idTable[annotation.id]

    if $scope.annotation.referrers?
      $scope.manage_new_data $scope.annotation.referrers, 'past'

    document.init_annotation = null
    $scope.open()

angular.module('h.displayer', imports)
.controller('DisplayerCtrl', Displayer)
