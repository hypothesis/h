var angular = require('angular');

// @ngInject
function AccountController($scope, $filter, auth, flash, formRespond, identity,
                           session) {
  var personaFilter = $filter('persona');

  $scope.subscriptionDescription = {
    reply: 'Someone replies to one of my annotations'
  };

  function onSuccess(form, response) {
    // Fire flash messages
    for (var type in response.flash) {
      response.flash[type].map(function (message) {
        flash[type](message);
      });
    }

    form.$setPristine();
    var formModel = form.$name.slice(0, -4);

    // Reset form fields
    $scope[formModel] = {};

    // Update status button
    $scope.$broadcast('formState', form.$name, 'success');
    $scope.email = response.email;
  };

  function onDelete(form, response) {
    identity.logout();
    onSuccess(form, response);
  };

  function onError(form, response) {
    if (response.status >= 400 && response.status < 500) {
      formRespond(form, response.data.errors);
    } else {
      if (response.data.flash) {
        for (type in response.data.flash) {
          response.data.flash[type].map(function (message) {
            flash[type](message);
          });
        }
      } else {
        flash.error('Sorry, we were unable to perform your request');
      }
    }

    // Update status button
    $scope.$broadcast('formState', form.$name, '');
  };

  $scope.tab = 'Account';
  session.profile().$promise.then(function(result) {
    $scope.subscriptions = result.subscriptions;
    $scope.email = result.email;
  });

  // Data for each of the forms
  $scope.editProfile = {};
  $scope.changePassword = {};
  $scope.deleteAccount = {};

  $scope.delete = function(form) {
    //  If the password is correct, the account is deleted.
    //  The extension is then removed from the page.
    //  Confirmation of success is given.
    if (!form.$valid) {
      return;
    }
    var username = personaFilter(auth.user);
    var packet = {
      username: username,
      pwd: form.pwd.$modelValue
    };

    var successHandler = angular.bind(null, onDelete, form);
    var errorHandler = angular.bind(null, onError, form);

    var promise = session.disable_user(packet).$promise;
    return promise.then(successHandler, errorHandler);
  };

  $scope.submit = function(form) {
    formRespond(form);
    if (!form.$valid) {
      return;
    }

    var username = personaFilter(auth.user);
    var packet = {
      username: username,
      pwd: form.pwd.$modelValue,
      password: form.password.$modelValue
    };

    var successHandler = angular.bind(null, onSuccess, form);
    var errorHandler = angular.bind(null, onError, form);

    // Update status button
    $scope.$broadcast('formState', form.$name, 'loading');

    var promise = session.edit_profile(packet).$promise;
    return promise.then(successHandler, errorHandler);
  };

  $scope.changeEmailSubmit = function(form) {
    formRespond(form);
    if (!form.$valid) {
      return;
    }

    var username = personaFilter(auth.user);
    var packet = {
      username: username,
      pwd: form.pwd.$modelValue,
      email: form.email.$modelValue,
      emailAgain: form.emailAgain.$modelValue
    };

    var successHandler = angular.bind(null, onSuccess, form);
    var errorHandler = angular.bind(null, onError, form);

    // Update status button
    $scope.$broadcast('formState', form.$name, 'loading');

    var promise = session.edit_profile(packet).$promise;
    return promise.then(successHandler, errorHandler);
  };

  $scope.updated = function(index, form) {
    var packet = {
      username: auth.user,
      subscriptions: JSON.stringify($scope.subscriptions[index])
    };

    var successHandler = angular.bind(null, onSuccess, form);
    var errorHandler = angular.bind(null, onError, form);

    var promise = session.edit_profile(packet).$promise;
    return promise.then(successHandler, errorHandler);
  };
}

module.exports = AccountController;
