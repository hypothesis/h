angular = require('angular')


module.exports = class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$route', '$scope', '$window',
    'auth', 'drafts', 'features', 'identity',
    'session', 'streamer', 'annotationUI',
    'annotationMapper', 'threading'
  ]
  constructor: (
     $controller,   $document,   $location,   $route,   $scope,   $window,
     auth,   drafts,   features,   identity,
     session,   streamer,   annotationUI,
     annotationMapper, threading
  ) ->
    $controller('AnnotationUIController', {$scope})

    # This stores information the current userid.
    # It is initially undefined until resolved.
    $scope.auth = user: undefined

    # Allow all child scopes to look up feature flags as:
    #
    #     if ($scope.feature('foo')) { ... }
    $scope.feature = features.flagEnabled

    # Allow all child scopes access to the session
    $scope.session = session

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

    # App dialogs
    $scope.accountDialog = visible: false
    $scope.shareDialog = visible: false

    # Check to see if we are on the stream page so we can hide share button.
    if $window.top is $window
      $scope.showShareButton = false
    else
      $scope.showShareButton = true

    cleanupAnnotations = ->
      # Clean up all the annotations
      for id, container of $scope.threading.idTable when container.message
        # Keep drafts. When logging out, drafts are already discarded.
        if drafts.contains(container.message)
          continue
        else
          $scope.$emit('annotationDeleted', container.message)

    identity.watch({
      onlogin: (identity) -> $scope.auth.user = auth.userid(identity)
      onlogout: -> $scope.auth.user = null
      onready: -> $scope.auth.user ?= null
    })

    $scope.$watch 'sort.name', (name) ->
      return unless name
      predicate = switch name
        when 'Newest' then ['-!!message', '-message.updated']
        when 'Oldest' then ['-!!message',  'message.updated']
        when 'Location' then (thread) ->
          if thread.message?
            for target in thread.message.target ? []
              for selector in target.selector ? []
                if selector.type is 'TextPositionSelector'
                  return selector.start
          return Number.POSITIVE_INFINITY
      $scope.sort = {name, predicate}

    $scope.$watch 'auth.user', (newVal, oldVal) ->
      return if newVal is oldVal

      if isFirstRun and not (newVal or oldVal)
        $scope.login()
      else
        $scope.accountDialog.visible = false

      # Reopen the streamer.
      streamer.close()
      streamer.open($window.WebSocket, streamerUrl)

      # Clean up annotations that should be removed.
      cleanupAnnotations()

      # Reload the view if this is not the initial load.
      if oldVal isnt undefined
        $route.reload()

    $scope.login = ->
      $scope.accountDialog.visible = true
      identity.request({
        oncancel: -> $scope.accountDialog.visible = false
      })

    $scope.logout = ->
      return unless drafts.discard()
      $scope.accountDialog.visible = false
      identity.logout()

    $scope.loadMore = (number) ->
      streamer.send({messageType: 'more_hits', moreHits: number})

    $scope.clearSelection = ->
      $scope.search.query = ''
      annotationUI.clearSelectedAnnotations()

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
