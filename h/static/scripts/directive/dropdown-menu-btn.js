'use strict';

// @ngInject
function PrimaryActionBtnController($scope, $timeout) {
  this.toggleDropdown = function($event) {
    $event.stopPropagation();
    $timeout(function () {
      $scope.onToggleDropdown();
    }, 0);
  }
}

module.exports = function () {
  return {
    controller: PrimaryActionBtnController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      label: '=',
      dropdownMenuLabel: '@',
      onToggleDropdown: '&',
    },
    templateUrl: 'dropdown_menu_btn.html'
  };
};
