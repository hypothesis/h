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
function annotationMapper($rootScope, threading, store, groups) {

  // All of the annotations that annotationMapper has received from calls to
  // its loadAnnotations() method.
  var received = [];

  // The annotations that are currently loaded into the page context.
  var loaded = [];

  function loadAnnotations(annotations) {
    received = received.concat(annotations);
    loadAnnotationsFromGroup(annotations, groups.focused().id);
  }

  function loadAnnotationsFromGroup(annotations, groupId) {
    // The annotations that we've added to the page.
    var newlyLoaded = [];

    annotations.forEach(function(annotation) {
      if (annotation.group !== groupId) {
        return;
      }

      var container = getContainer(threading, annotation);
      if (container !== null) {
        angular.copy(annotation, container.message);
        $rootScope.$emit('annotationUpdated', container.message);
        return;
      }

      newlyLoaded.push(new store.AnnotationResource(annotation));
    });

    $rootScope.$emit('annotationsLoaded', newlyLoaded);
    loaded = loaded.concat(newlyLoaded);
  }

  // When the focused group changes, change what annotations are shown.
  $rootScope.$on('groupFocused', function() {
    unloadAnnotations(loaded);
    loadAnnotationsFromGroup(received, groups.focused().id);
  });

  function unloadAnnotations(annotations) {
    annotations.forEach(function(annotation) {
      var container = getContainer(threading, annotation);
      if (container !== null && annotation !== container.message) {
        annotation = angular.copy(annotation, container.message);
      }

      $rootScope.$emit('annotationDeleted', annotation);
    });

    annotations.slice().forEach(function(annotation) {
      loaded.splice(loaded.indexOf(annotation, 1));
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
