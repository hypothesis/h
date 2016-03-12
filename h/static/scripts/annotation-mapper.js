'use strict';

var angular = require('angular');

var events = require('./events');

function getExistingAnnotation(annotationUI, id) {
  return annotationUI.annotations.find(function (annot) {
    return annot.id === id;
  });
}

// Wraps the annotation store to trigger events for the CRUD actions
// @ngInject
function annotationMapper($rootScope, annotationUI, store) {
  function loadAnnotations(annotations, replies) {
    annotations = annotations.concat(replies || []);

    var loaded = [];
    annotations.forEach(function (annotation) {
      var existing = getExistingAnnotation(annotationUI, annotation.id);
      if (existing) {
        angular.copy(annotation, existing);
        $rootScope.$emit(events.ANNOTATION_UPDATED, existing);
        return;
      }
      loaded.push(new store.AnnotationResource(annotation));
    });

    $rootScope.$emit(events.ANNOTATIONS_LOADED, loaded);
  }

  function unloadAnnotations(annotations) {
    var unloaded = annotations.map(function (annotation) {
      var existing = getExistingAnnotation(annotationUI, annotation.id);
      if (existing && annotation !== existing) {
        annotation = angular.copy(annotation, existing);
      }
      return annotation;
    });
    $rootScope.$emit(events.ANNOTATIONS_UNLOADED, unloaded);
  }

  function createAnnotation(annotation) {
    annotation = new store.AnnotationResource(annotation);
    $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED, annotation);
    return annotation;
  }

  function deleteAnnotation(annotation) {
    return annotation.$delete({
      id: annotation.id
    }).then(function () {
      $rootScope.$emit(events.ANNOTATION_DELETED, annotation);
      return annotation;
    });
  }

  return {
    loadAnnotations: loadAnnotations,
    unloadAnnotations: unloadAnnotations,
    createAnnotation: createAnnotation,
    deleteAnnotation: deleteAnnotation
  };
}


module.exports = annotationMapper;
