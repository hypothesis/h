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

  this.setShared = function () {
    $scope.onSetPrivacy({level: 'shared'});
  }

  this.setPrivate = function () {
    $scope.onSetPrivacy({level: 'private'});
  }

  function updatePublishActionLabel() {
    if ($scope.isShared) {
      vm.publishDestination = vm.group.name;
    } else {
      vm.publishDestination = vm.privateLabel;
    }
  }
  $scope.$watch('isShared', function () {
    updatePublishActionLabel();
  });
}

module.exports = function () {
  return {
    controller: PublishAnnotationBtnController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      group: '=',
      isShared: '=',
      onSave: '&',
      onSetPrivacy: '&'
    },
    templateUrl: 'publish_annotation_btn.html'
  };
}
