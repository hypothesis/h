'use strict';

/** Watch the UI state and update scope properties. */
// @ngInject
function AnnotationUIController($rootScope, $scope, annotationUI) {
  $rootScope.$watch(function () {
    return annotationUI.selectedAnnotationMap;
  }, function (map) {
    map = map || {};
    var count = Object.keys(map).length;
    $scope.selectedAnnotationsCount = count;

    if (count) {
      $scope.selectedAnnotations = map;
    } else {
      $scope.selectedAnnotations = null;
    }
  });

  $rootScope.$watch(function () {
    return annotationUI.focusedAnnotationMap;
  }, function (map) {
    map = map || {};
    $scope.focusedAnnotations = map;
  });

  $rootScope.$on('annotationDeleted', function (event, annotation) {
    annotationUI.removeSelectedAnnotation(annotation);
  });
}

module.exports = AnnotationUIController;
