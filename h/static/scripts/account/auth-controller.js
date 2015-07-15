var AuthController = (function() {
  AuthController.$inject = ['$scope', '$timeout', 'flash', 'session',
    'formRespond'];

  function AuthController($scope, $timeout, flash, session, formRespond) {
    var failure, success, timeout;
    timeout = null;
    success = function(data) {
      var _ref;
      if (data.userid) {
        $scope.$emit('auth', null, data);
      }
      $scope.account.tab = (function() {
        switch ($scope.account.tab) {
          case 'register':
            return 'login';
          case 'forgot_password':
            return 'reset_password';
          case 'reset_password':
            return 'login';
          default:
            return $scope.account.tab;
        }
      })();
      angular.copy({}, $scope.model);
      return (_ref = $scope.form) != null ? _ref.$setPristine() : void 0;
    };
    failure = function(form, response) {
      var errors, reason, _ref;
      try {
        _ref = response.data, errors = _ref.errors, reason = _ref.reason;
      } catch (_error) {
        reason = "Oops, something went wrong on the server. Please try again later!";
      }
      return formRespond(form, errors, reason);
    };
    this.submit = function(form) {
      formRespond(form);
      if (!form.$valid) {
        return;
      }
      $scope.$broadcast('formState', form.$name, 'loading');
      return session[form.$name]($scope.model, success, angular.bind(this, failure, form)).$promise.finally(function() {
        return $scope.$broadcast('formState', form.$name, '');
      });
    };
    if ($scope.account == null) {
      $scope.account = {
        tab: 'login'
      };
    }
    if ($scope.model == null) {
      $scope.model = {};
    }
    $scope.$on('auth', (function() {
      var preventCancel;
      return preventCancel = $scope.$on('$destroy', function() {
        if (timeout) {
          $timeout.cancel(timeout);
        }
        return $scope.$emit('auth', 'cancel');
      });
    })());
    $scope.$watchCollection('model', function(value) {
      if (timeout) {
        $timeout.cancel(timeout);
      }
      if (value && !angular.equals(value, {})) {
        return timeout = $timeout(function() {
          var _ref;
          angular.copy({}, $scope.model);
          if ((_ref = $scope.form) != null) {
            _ref.$setPristine();
          }
          return flash.info('For your security, the forms have been reset due to inactivity.');
        }, 300000);
      }
    });
  }

  return AuthController;

})();

angular.module('h').controller('AuthController', AuthController);
