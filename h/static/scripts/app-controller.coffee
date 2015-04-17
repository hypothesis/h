angular = require('angular')


module.exports = class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$rootScope', '$route', '$scope',
    '$window',
    'auth', 'drafts', 'identity',
    'permissions', 'streamer', 'annotationUI'
  ]
  constructor: (
     $controller,   $document,   $location,   $rootScope,   $route,   $scope,
     $window,
     auth,   drafts,   identity,
     permissions,   streamer,   annotationUI
  ) ->
    $controller('AnnotationUIController', {$scope})

    $scope.auth = auth
    isFirstRun = $location.search().hasOwnProperty('firstrun')

    streamerUrl = new URL('/ws', $document.prop('baseURI'))
    streamerUrl.protocol = streamerUrl.protocol.replace('http', 'ws')
    streamerUrl = streamerUrl.href

    oncancel = ->
      $scope.dialog.visible = false

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
      $rootScope.$emit 'cleanupAnnotations'

      # Reload the view.
      $route.reload()

    $rootScope.$on 'beforeAnnotationCreated', ->
      $scope.clearSelection()

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
