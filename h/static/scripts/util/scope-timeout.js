'use strict';

/**
 * Sets a timeout which is linked to the lifetime of an Angular scope.
 *
 * When the scope is destroyed, the timeout will be cleared if it has
 * not already fired.
 *
 * The callback is not invoked within a $scope.$apply() context. It is up
 * to the caller to do that if necessary.
 *
 * @param {Scope} $scope - An Angular scope
 * @param {Function} fn - Callback to invoke with setTimeout
 * @param {number} delay - Delay argument to pass to setTimeout
 */
module.exports = function ($scope, fn, delay, setTimeoutFn, clearTimeoutFn) {
  setTimeoutFn = setTimeoutFn || setTimeout;
  clearTimeoutFn = clearTimeoutFn || clearTimeout;

  var removeDestroyHandler;
  var id = setTimeoutFn(function () {
    removeDestroyHandler();
    fn();
  }, delay);
  removeDestroyHandler = $scope.$on('$destroy', function () {
    clearTimeoutFn(id);
  });
};
