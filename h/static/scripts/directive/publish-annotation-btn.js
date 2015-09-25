'use strict';

var STORAGE_KEY = 'hypothesis.privacy';

// @ngInject
function PublishAnnotationBtnController($scope, localStorage) {
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

  this.setPrivacy = function (level) {
    localStorage.setItem(STORAGE_KEY, level);
    $scope.onSetPrivacy({level: level});
  }

  $scope.$watch('isShared', function () {
    updatePublishActionLabel();
  });

  if ($scope.isNew) {
    // set the privacy level for new annotations.
    // FIXME - This should be done at the time the annotation is created,
    // not by this control
    var defaultLevel = localStorage.getItem(STORAGE_KEY);
    if (defaultLevel !== 'private' &&
        defaultLevel !== 'shared') {
      defaultLevel = 'shared';
    }
    this.setPrivacy(defaultLevel);
  }

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
      onSave: '&',
      onSetPrivacy: '&'
    },
    templateUrl: 'publish_annotation_btn.html'
  };
}
