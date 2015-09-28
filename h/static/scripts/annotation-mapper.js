'use strict';


// Fetch the container object for the passed annotation from the threading
// service, but only return it if it has an associated message.
function getContainer(threading, annotation) {
  var container = threading.idTable[annotation.id];
  if (container === null || typeof container === 'undefined') {
    return null;
  }
  // Also return null if the container has no message
  if (!container.message) {
    return null;
  }
  return container;
}


// Wraps the annotation store to trigger events for the CRUD actions
// @ngInject
function annotationMapper($rootScope, threading, store) {
  function loadAnnotations(annotations) {
    var loaded = [];

    annotations.forEach(function (annotation) {
      var container = getContainer(threading, annotation);
      if (container !== null) {
        angular.copy(annotation, container.message);
        $rootScope.$emit('annotationUpdated', container.message);
        return;
      }

      loaded.push(new store.AnnotationResource(annotation));
    });

    $rootScope.$emit('annotationsLoaded', loaded);
  }

  function unloadAnnotations(annotations) {
    annotations.forEach(function (annotation) {
      var container = getContainer(threading, annotation);
      if (container !== null && annotation !== container.message) {
        annotation = angular.copy(annotation, container.message);
      }

      $rootScope.$emit('annotationDeleted', annotation);
    });
  }

  function createAnnotation(annotation) {
    annotation = new store.AnnotationResource(annotation);
    $rootScope.$emit('beforeAnnotationCreated', annotation);
    return annotation;
  }

  function deleteAnnotation(annotation) {
    return annotation.$delete({
      id: annotation.id
    }).then(function () {
      $rootScope.$emit('annotationDeleted', annotation);
      return annotation;
    });
  }

  return {
    loadAnnotations: loadAnnotations,
    unloadAnnotations: unloadAnnotations,
    createAnnotation: createAnnotation,
    deleteAnnotation: deleteAnnotation,
    threads: function() {
      return threading.root.children;
    },
    thread: function(id) {
      return threading.idTable[id];
    }
  };
}


module.exports = annotationMapper;
