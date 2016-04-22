'use strict';

var angular = require('angular');
var scrollIntoView = require('scroll-into-view');

var annotationMetadata = require('./annotation-metadata');
var events = require('./events');
var parseAccountID = require('./filter/persona').parseAccountID;
var scopeTimeout = require('./util/scope-timeout');

function authStateFromUserID(userid) {
  if (userid) {
    var parsed = parseAccountID(userid);
    return {
      status: 'signed-in',
      userid: userid,
      username: parsed.username,
      provider: parsed.provider,
    };
  } else {
    return {status: 'signed-out'};
  }
}

// @ngInject
module.exports = function AppController(
  $controller, $document, $location, $rootScope, $route, $scope,
  $window, annotationUI, auth, drafts, features, groups,
  session, settings
) {

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

  // App dialogs
  $scope.accountDialog = {visible: false};
  $scope.shareDialog = {visible: false};
  $scope.aboutThisVersionDialog = {visible: false};

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
    $scope.auth = authStateFromUserID(data.userid);
    $scope.accountDialog.visible = false;

    if (!data || !data.initialLoad) {
      $route.reload();
    }
  });

  session.load().then(function (state) {
    // When the authentication status of the user is known,
    // update the auth info in the top bar and show the login form
    // after first install of the extension.
    $scope.auth = authStateFromUserID(state.userid);
    if (!state.userid && settings.firstRun) {
      $scope.login();
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
        predicateFn = function (thread) {
          return annotationMetadata.location(thread.message);
        };
        break;
    }
    $scope.sort = {
      name: name,
      predicate: predicateFn,
      options: $scope.sort.options,
    };
  });

  /** Scroll to the view to the element matching the given selector */
  function scrollToView(selector) {
    // Add a timeout so that if the element has just been shown (eg. via ngIf)
    // it is added to the DOM before we try to locate and scroll to it.
    scopeTimeout($scope, function () {
      scrollIntoView($document[0].querySelector(selector));
    }, 0);
  }

  // Start the login flow. This will present the user with the login dialog.
  $scope.login = function () {
    $scope.accountDialog.visible = true;
    scrollToView('login-form');
  };

  // Display the dialog for sharing the current page
  $scope.share = function () {
    $scope.shareDialog.visible = true;
    scrollToView('share-dialog');
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
    if (!promptToLogout()) {
      return;
    }
    drafts.unsaved().forEach(function (draft) {
      $rootScope.$emit(events.ANNOTATION_DELETED, draft);
    });
    drafts.discard();
    $scope.accountDialog.visible = false;
    return auth.logout();
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
