'use strict';

var dateUtil = require('../date-util');

// @ngInject
function TimestampController($scope, time) {
  var vm = this;

  // A fuzzy, relative (eg. '6 days ago') format of the timestamp.
  vm.relativeTimestamp = null;

  // A formatted version of the timestamp (eg. 'Tue 22nd Dec 2015, 16:00')
  vm.absoluteTimestamp = '';

  var cancelTimestampRefresh;

  function updateTimestamp() {
    vm.relativeTimestamp = time.toFuzzyString(vm.timestamp);
    vm.absoluteTimestamp = dateUtil.format(new Date(vm.timestamp));

    if (vm.timestamp) {
      if (cancelTimestampRefresh) {
        cancelTimestampRefresh();
      }
      cancelTimestampRefresh = time.decayingInterval(vm.timestamp, function () {
        updateTimestamp();
        $scope.$digest();
      });
    }
  }

  this.$onChanges = function (changes) {
    if (changes.timestamp) {
      updateTimestamp();
    }
  };

  this.$onDestroy = function () {
    if (cancelTimestampRefresh) {
      cancelTimestampRefresh();
    }
  };
}

module.exports = function () {
  return {
    bindToController: true,
    controller: TimestampController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      className: '<',
      href: '<',
      timestamp: '<',
    },
    template: ['<a class="{{vm.className}}" target="_blank" ng-title="vm.absoluteTimestamp"',
               ' href="{{vm.href}}"',
               '>{{vm.relativeTimestamp}}</a>'].join(''),
  };
};
