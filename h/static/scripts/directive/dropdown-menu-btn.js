'use strict';

// @ngInject
function DropdownMenuBtnController($scope, $timeout) {
  this.toggleDropdown = function($event) {
    $event.stopPropagation();
    $timeout(function () {
      $scope.onToggleDropdown();
    }, 0);
  }
}

module.exports = function () {
  return {
    controller: DropdownMenuBtnController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      isDisabled: '=',
      label: '=',
      dropdownMenuLabel: '@',
      onToggleDropdown: '&',
    },
    templateUrl: 'dropdown_menu_btn.html'
  };
};
