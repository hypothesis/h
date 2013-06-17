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
      new StreamerFilter()
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
      $scope.sock = new SockJSWrapper $scope, $scope.filter
      , null
      , $scope.manage_new_data
      ,=>
        $timeout $scope.open, 5000

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
