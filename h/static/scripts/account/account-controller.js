var AccountController;
var __hasProp = {}.hasOwnProperty;

AccountController = (function() {
  AccountController.inject = ['$scope', '$filter', 'auth', 'flash',
    'formRespond', 'identity', 'session'];

  function AccountController($scope, $filter, auth, flash, formRespond,
      identity, session) {
    var onDelete;
    var onError;
    var onSuccess;
    var personaFilter = $filter('persona');
    $scope.subscriptionDescription = {
      reply: 'Someone replies to one of my annotations'
    };
    onSuccess = function(form, response) {
      var formModel;
      var m;
      var msgs;
      var type;
      var ref = response.flash;
      for (type in ref) {
        msgs = ref[type];
        for (var i = 0; i < msgs.length; i++) {
          m = msgs[i];
          flash[type](m);
        }
      }
      form.$setPristine();
      formModel = form.$name.slice(0, -4);
      $scope[formModel] = {};
      $scope.$broadcast('formState', form.$name, 'success');
      return $scope.email = response.email;
    };
    onDelete = function(form, response) {
      identity.logout();
      return onSuccess(form, response);
    };
    onError = function(form, response) {
      var m;
      var msgs;
      var type;
      if (response.status >= 400 && response.status < 500) {
        formRespond(form, response.data.errors);
      } else {
        if (response.data.flash) {
          var ref = response.data.flash;
          for (type in ref) {
            if (!__hasProp.call(ref, type)) {
              continue;
            }
            msgs = ref[type];
            for (var i = 0; i < msgs.length; i++) {
              m = msgs[i];
              flash[type](m);
            }
          }
        } else {
          flash.error('Sorry, we were unable to perform your request');
        }
      }
      return $scope.$broadcast('formState', form.$name, '');
    };
    $scope.tab = 'Account';
    session.profile().$promise.then((function() {
      return function(result) {
        $scope.subscriptions = result.subscriptions;
        return $scope.email = result.email;
      };
    })(this));
    $scope.editProfile = {};
    $scope.changePassword = {};
    $scope.deleteAccount = {};
    $scope.delete = function(form) {
      var errorHandler;
      var packet;
      var promise;
      var successHandler;
      var username;
      if (!form.$valid) {
        return;
      }
      username = personaFilter(auth.user);
      packet = {
        username: username,
        pwd: form.pwd.$modelValue
      };
      successHandler = angular.bind(null, onDelete, form);
      errorHandler = angular.bind(null, onError, form);
      promise = session.disable_user(packet);
      return promise.$promise.then(successHandler, errorHandler);
    };
    $scope.submit = function(form) {
      var errorHandler;
      var packet;
      var promise;
      var successHandler;
      var username;
      formRespond(form);
      if (!form.$valid) {
        return;
      }
      username = personaFilter(auth.user);
      packet = {
        username: username,
        pwd: form.pwd.$modelValue,
        password: form.password.$modelValue
      };
      successHandler = angular.bind(null, onSuccess, form);
      errorHandler = angular.bind(null, onError, form);
      $scope.$broadcast('formState', form.$name, 'loading');
      promise = session.edit_profile(packet);
      return promise.$promise.then(successHandler, errorHandler);
    };
    $scope.changeEmailSubmit = function(form) {
      var errorHandler;
      var packet;
      var promise;
      var successHandler;
      var username;
      formRespond(form);
      if (!form.$valid) {
        return;
      }
      username = personaFilter(auth.user);
      packet = {
        username: username,
        pwd: form.pwd.$modelValue,
        email: form.email.$modelValue,
        emailAgain: form.emailAgain.$modelValue
      };
      successHandler = angular.bind(null, onSuccess, form);
      errorHandler = angular.bind(null, onError, form);
      $scope.$broadcast('formState', form.$name, 'loading');
      promise = session.edit_profile(packet);
      return promise.$promise.then(successHandler, errorHandler);
    };
    $scope.updated = function(index, form) {
      var errorHandler;
      var packet;
      var promise;
      var successHandler;
      packet = {
        username: auth.user,
        subscriptions: JSON.stringify($scope.subscriptions[index])
      };
      successHandler = angular.bind(null, onSuccess, form);
      errorHandler = angular.bind(null, onError, form);
      promise = session.edit_profile(packet);
      return promise.$promise.then(successHandler, errorHandler);
    };
  }

  return AccountController;

})();

angular.module('h').controller('AccountController', AccountController);
