angular = require('angular')


module.exports = class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$route', '$scope', '$window',
    'annotationUI', 'auth', 'drafts', 'features', 'identity', 'session'
  ]
  constructor: (
     $controller,   $document,   $location,   $route,   $scope,   $window,
     annotationUI,   auth,   drafts,   features,   identity,  session
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

    # App dialogs
    $scope.accountDialog = visible: false
    $scope.shareDialog = visible: false

    # Check to see if we are on the stream page so we can hide share button.
    $scope.isEmbedded = $window.top isnt $window

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
