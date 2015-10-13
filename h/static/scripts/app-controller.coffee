angular = require('angular')

events = require('./events');

module.exports = class AppController
  this.$inject = [
    '$controller', '$document', '$location', '$route', '$scope', '$window',
    'annotationUI', 'auth', 'drafts', 'features', 'groups', 'identity',
    'session'
  ]
  constructor: (
     $controller,   $document,   $location,   $route,   $scope,   $window,
     annotationUI,   auth,   drafts,   features,   groups,   identity,
     session
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

    # Check to see if we're in the sidebar, or on a standalone page such as
    # the stream page or an individual annotation page.
    $scope.isSidebar = $window.top isnt $window

    # Default sort
    $scope.sort = name: 'Location'

    # Reload the view when the focused group changes or the
    # list of groups that the user is a member of changes
    reloadEvents = [events.SESSION_CHANGED, events.GROUP_FOCUSED];
    reloadEvents.forEach((eventName) ->
      $scope.$on(eventName, (event) ->
        $route.reload()
      )
    );

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
