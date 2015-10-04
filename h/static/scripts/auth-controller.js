// @ngInject
function AuthController($scope, $timeout, flash, session, formRespond) {
  var pendingTimeout = null;

  function success(data) {
    if (data.userid) {
      $scope.$emit('auth', null, data);
    }

    angular.copy({}, $scope.model);

    if ($scope.form != null) {
      $scope.form.$setPristine()
    }
  };

  function failure(form, response) {
    var errors, reason;

    try {
      errors = response.data.errors;
      reason = response.data.reason;
    } catch (e) {
      reason = 'Oops, something went wrong on the server. ' +
        'Please try again later!';
    }

    return formRespond(form, errors, reason);
  };

  function timeout() {
    angular.copy({}, $scope.model);

    if ($scope.form != null) {
      $scope.form.$setPristine();
    }

    flash.info('For your security, ' +
               'the forms have been reset due to inactivity.');
  }

  function cancelTimeout() {
    if (pendingTimeout == null) {
      return;
    }
    $timeout.cancel(pendingTimeout);
    pendingTimeout = null;
  }


  this.submit = function submit(form) {
    formRespond(form);
    if (!form.$valid) {
      return;
    }

    $scope.$broadcast('formState', form.$name, 'loading');

    var handler = session[form.$name];
    var _failure = angular.bind(this, failure, form);
    var res = handler($scope.model, success, _failure);

    res.$promise.finally(function() {
      return $scope.$broadcast('formState', form.$name, '');
    });
  };

  if ($scope.model == null) {
    $scope.model = {};
  }

  // Stop the inactivity timeout when the scope is destroyed.
  var removeDestroyHandler = $scope.$on('$destroy', function () {
    cancelTimeout(pendingTimeout);
    $scope.$emit('auth', 'cancel');
  });

  // Skip the cancel when destroying the scope after a successful auth.
  $scope.$on('auth', removeDestroyHandler);

  // Reset the auth forms afterfive minutes of inactivity.
  $scope.$watchCollection('model', function(value) {
    cancelTimeout(pendingTimeout);
    if (value && !angular.equals(value, {})) {
      pendingTimeout = $timeout(timeout, 300000);
    }
  });
}

module.exports = AuthController;
