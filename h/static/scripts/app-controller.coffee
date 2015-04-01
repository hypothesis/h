angular = require('angular')


module.exports = class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$rootScope', '$route', '$scope',
    '$window',
    'auth', 'drafts', 'identity',
    'permissions', 'streamer', 'annotationUI',
    'annotationMapper', 'threading'
  ]
  constructor: (
     $controller,   $document,   $location,   $rootScope,   $route,   $scope,
     $window,
     auth,   drafts,   identity,
     permissions,   streamer,   annotationUI,
     annotationMapper, threading
  ) ->
    $controller('AnnotationUIController', {$scope})

    $scope.auth = auth
    isFirstRun = $location.search().hasOwnProperty('firstrun')

    streamerUrl = new URL('/ws', $document.prop('baseURI'))
    streamerUrl.protocol = streamerUrl.protocol.replace('http', 'ws')
    streamerUrl = streamerUrl.href

    applyUpdates = (action, data) ->
      # Update the application with new data from the websocket.
      return unless data?.length
      switch action
        when 'create', 'update', 'past'
          annotationMapper.loadAnnotations data
        when 'delete'
          for annotation in data
            if a = threading.idTable[annotation.id]?.message
              $scope.$emit('annotationDeleted', a)

    streamer.onmessage = (data) ->
      return if !data or data.type != 'annotation-notification'
      action = data.options.action
      payload = data.payload
      applyUpdates(action, payload)
      $scope.$digest()

    oncancel = ->
      $scope.dialog.visible = false

    cleanupAnnotations = ->
      # Clean up any annotations that need to be unloaded.
      for id, container of $scope.threading.idTable when container.message
        # Remove annotations the user is not authorized to view.
        if not permissions.permits 'read', container.message, auth.user
          $scope.$emit('annotationDeleted', container.message)
          drafts.remove container.message

    $scope.$watch 'sort.name', (name) ->
      return unless name
      predicate = switch name
        when 'Newest' then ['-!!message', '-message.updated']
        when 'Oldest' then ['-!!message',  'message.updated']
        when 'Location' then ['-!!message', 'message.target[0].pos.top']
      $scope.sort = {name, predicate}

    $scope.$watch (-> auth.user), (newVal, oldVal) ->
      return if newVal is oldVal

      if isFirstRun and not (newVal or oldVal)
        $scope.login()
      else
        $scope.dialog.visible = false

      # Update any edits in progress.
      for draft in drafts.all()
        $scope.$emit('beforeAnnotationCreated', draft)

      # Reopen the streamer.
      streamer.close()
      streamer.open($window.WebSocket, streamerUrl)

      # Clean up annotations that should be removed
      cleanupAnnotations()

      # Reload the view.
      $route.reload()

    $rootScope.$on 'beforeAnnotationCreated', ->
      $scope.clearSelection()

    $rootScope.$on 'editorOpened', (annotation) ->
      $rootScope.scrollTo(annotation)

    $scope.login = ->
      $scope.dialog.visible = true
      identity.request {oncancel}

    $scope.logout = ->
      return unless drafts.discard()
      $scope.dialog.visible = false
      identity.logout()

    $scope.loadMore = (number) ->
      streamer.send({messageType: 'more_hits', moreHits: number})

    $scope.clearSelection = ->
      $scope.search.query = ''
      annotationUI.clearSelectedAnnotations()

    $scope.dialog = visible: false

    $scope.search =
      query: $location.search()['q']

      clear: ->
        $location.search('q', null)

      update: (query) ->
        unless angular.equals $location.search()['q'], query
          $location.search('q', query or null)
          annotationUI.clearSelectedAnnotations()

    $scope.sort = name: 'Location'
    $scope.threading = threading
    $scope.threadRoot = $scope.threading?.root
