'use strict';

var events = require('./events');

/** Watch the UI state and update scope properties. */
// @ngInject
function AnnotationUIController($rootScope, $scope, annotationUI) {
  annotationUI.subscribe(function () {
    var state = annotationUI.getState();

    $scope.selectedAnnotations = state.selectedAnnotationMap;

    if (state.selectedAnnotationMap) {
      $scope.selectedAnnotationsCount =
        Object.keys(state.selectedAnnotationMap).length;
    } else {
      $scope.selectedAnnotationsCount = 0;
    }

    $scope.focusedAnnotations = state.focusedAnnotationMap;
  });

  $rootScope.$on(events.ANNOTATION_DELETED, function (event, annotation) {
    annotationUI.removeSelectedAnnotation(annotation);
  });
}

module.exports = AnnotationUIController;
