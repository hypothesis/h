'use strict';

// @ngInject
function PublishAnnotationBtnController($scope) {
  var vm = this;

  vm.group = {
    name: $scope.group.name,
    type: $scope.group.public ? 'public' : 'group'
  };
  vm.showDropdown = false;
  vm.privateLabel = 'Only Me';

  updatePublishActionLabel();

  this.save = function () {
    $scope.onSave();
  };

  this.cancel = function () {
    $scope.onCancel();
  }

  this.setPrivacy = function (level) {
    $scope.onSetPrivacy({level: level});
  }

  $scope.$watch('isShared', function () {
    updatePublishActionLabel();
  });

  function updatePublishActionLabel() {
    if ($scope.isShared) {
      vm.publishDestination = vm.group.name;
    } else {
      vm.publishDestination = vm.privateLabel;
    }
  }
}

/**
 * @ngdoc directive
 * @name publishAnnotationBtn
 * @description Displays a combined privacy/selection post button to post
 *              a new annotation
 */
// @ngInject
module.exports = function () {
  return {
    controller: PublishAnnotationBtnController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      group: '=',
      canPost: '=',
      isShared: '=',
      isNew: '=',
      onCancel: '&',
      onSave: '&',
      onSetPrivacy: '&'
    },
    templateUrl: 'publish_annotation_btn.html'
  };
}
