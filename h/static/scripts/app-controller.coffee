angular = require('angular')

events = require('./events')
parseAccountID = require('./filter/persona').parseAccountID

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

    # This stores information about the current user's authentication status.
    # When the controller instantiates we do not yet know if the user is
    # logged-in or not, so it has an initial status of 'unknown'. This can be
    # used by templates to show an intermediate or loading state.
    $scope.auth = {status: 'unknown'}

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
    $scope.sort = {
      name: 'Location'
      options: ['Newest', 'Oldest', 'Location']
    }

    # Reload the view when the user switches accounts
    reloadEvents = [events.USER_CHANGED];
    reloadEvents.forEach((eventName) ->
      $scope.$on(eventName, (event, data) ->
        if !data || !data.initialLoad
          $route.reload()
      )
    );

    identity.watch({
      onlogin: (identity) ->
        # Hide the account dialog
        $scope.accountDialog.visible = false
        # Update the current logged-in user information
        userid = auth.userid(identity)
        parsed = parseAccountID(userid)
        angular.copy({
          status: 'signed-in',
          userid: userid,
          username: parsed.username,
          provider: parsed.provider,
        }, $scope.auth)
      onlogout: ->
        angular.copy({status: 'signed-out'}, $scope.auth)
      onready: ->
        # If their status is still 'unknown', then `onlogin` wasn't called and
        # we know the current user isn't signed in.
        if $scope.auth.status == 'unknown'
          angular.copy({status: 'signed-out'}, $scope.auth)
          if isFirstRun
            $scope.login()
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
      $scope.sort = {
        name,
        predicate,
        options: $scope.sort.options,
      }

    # Start the login flow. This will present the user with the login dialog.
    $scope.login = ->
      $scope.accountDialog.visible = true
      identity.request({
        oncancel: -> $scope.accountDialog.visible = false
      })

    # Log the user out.
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
