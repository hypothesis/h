'use strict';

var angular = require('angular');

var annotationMetadata = require('./annotation-metadata');
var events = require('./events');
var parseAccountID = require('./filter/persona').parseAccountID;

// @ngInject
module.exports = function AppController(
  $controller, $document, $location, $rootScope, $route, $scope,
  $window, annotationUI, auth, drafts, features, groups,
  identity, session
) {
  $controller('AnnotationUIController', {$scope: $scope});

  // This stores information about the current user's authentication status.
  // When the controller instantiates we do not yet know if the user is
  // logged-in or not, so it has an initial status of 'unknown'. This can be
  // used by templates to show an intermediate or loading state.
  $scope.auth = {status: 'unknown'};

  // Allow all child scopes to look up feature flags as:
  //
  //     if ($scope.feature('foo')) { ... }
  $scope.feature = features.flagEnabled;

  // Allow all child scopes access to the session
  $scope.session = session;

  var isFirstRun = $location.search().hasOwnProperty('firstrun');

  // App dialogs
  $scope.accountDialog = {visible: false};
  $scope.shareDialog = {visible: false};

  // Check to see if we're in the sidebar, or on a standalone page such as
  // the stream page or an individual annotation page.
  $scope.isSidebar = $window.top !== $window;

  // Default sort
  $scope.sort = {
    name: 'Location',
    options: ['Newest', 'Oldest', 'Location']
  };

  // Reload the view when the user switches accounts
  $scope.$on(events.USER_CHANGED, function (event, data) {
    if (!data || !data.initialLoad) {
      $route.reload();
    }
  });

  identity.watch({
    onlogin: function (identity) {
      // Hide the account dialog
      $scope.accountDialog.visible = false;
      // Update the current logged-in user information
      var userid = auth.userid(identity);
      var parsed = parseAccountID(userid);
      angular.copy({
        status: 'signed-in',
        userid: userid,
        username: parsed.username,
        provider: parsed.provider,
      }, $scope.auth);
    },
    onlogout: function () {
      angular.copy({status: 'signed-out'}, $scope.auth);
    },
    onready: function () {
      // If their status is still 'unknown', then `onlogin` wasn't called and
      // we know the current user isn't signed in.
      if ($scope.auth.status === 'unknown') {
        angular.copy({status: 'signed-out'}, $scope.auth);
        if (isFirstRun) {
          $scope.login();
        }
      }
    }
  });

  $scope.$watch('sort.name', function (name) {
    if (!name) {
      return;
    }
    var predicateFn;
    switch (name) {
      case 'Newest':
        predicateFn = ['-!!message', '-message.updated'];
        break;
      case 'Oldest':
        predicateFn = ['-!!message', 'message.updated'];
        break;
      case 'Location':
        predicateFn = annotationMetadata.location;
        break;
    }
    $scope.sort = {
      name: name,
      predicate: predicateFn,
      options: $scope.sort.options,
    };
  });

  // Start the login flow. This will present the user with the login dialog.
  $scope.login = function () {
    $scope.accountDialog.visible = true;
    return identity.request({
      oncancel: function () { $scope.accountDialog.visible = false; }
    });
  };

  // Prompt to discard any unsaved drafts.
  var promptToLogout = function () {
    // TODO - Replace this with a UI which doesn't look terrible.
    var text = '';
    if (drafts.count() === 1) {
      text = 'You have an unsaved annotation.\n' +
        'Do you really want to discard this draft?';
    } else if (drafts.count() > 1) {
      text = 'You have ' + drafts.count() + ' unsaved annotations.\n' +
        'Do you really want to discard these drafts?';
    }
    return (drafts.count() === 0 || $window.confirm(text));
  };

  // Log the user out.
  $scope.logout = function () {
    if (promptToLogout()) {
      var iterable = drafts.unsaved();
      for (var i = 0, draft; i < iterable.length; i++) {
        draft = iterable[i];
        $rootScope.$emit("annotationDeleted", draft);
      }
      drafts.discard();
      $scope.accountDialog.visible = false;
      return identity.logout();
    }
  };

  $scope.clearSelection = function () {
    $scope.search.query = '';
    annotationUI.clearSelectedAnnotations();
  };

  $scope.search = {
    query: $location.search().q,
    clear: function () {
      $location.search('q', null);
    },
    update: function (query) {
      if (!angular.equals($location.search().q, query)) {
        $location.search('q', query || null);
        annotationUI.clearSelectedAnnotations();
      }
    }
  };
};
