'use strict';

var events = require('./events');

/**
 * Returns the already-loaded annotation with a given ID,
 * if there is one.
 *
 * @param {string} id
 * @return {Annotation?} The existing Annotation instance
 */
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
      if (getExistingAnnotation(annotationUI, annotation.id)) {
        $rootScope.$emit(events.ANNOTATION_UPDATED, annotation);
        return;
      }
      loaded.push(new store.AnnotationResource(annotation));
    });

    $rootScope.$emit(events.ANNOTATIONS_LOADED, loaded);
  }

  function unloadAnnotations(annotations) {
    $rootScope.$emit(events.ANNOTATIONS_UNLOADED, annotations);
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
