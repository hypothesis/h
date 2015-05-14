# Wraps the annotation store to trigger events for the CRUD actions
module.exports = [
  '$rootScope', 'threading', 'store',
  ($rootScope, threading, store) ->
    setupAnnotation: (ann) -> ann

    loadAnnotations: (annotations) ->
      annotations = for annotation in annotations
        container = threading.idTable[annotation.id]
        if container?.message
          angular.copy(annotation, container.message)
          $rootScope.$emit('annotationUpdated', container.message)
          continue
        else
          annotation

      annotations = (new store.AnnotationResource(a) for a in annotations)
      $rootScope.$emit('annotationsLoaded', annotations)

    createAnnotation: (annotation) ->
      annotation = new store.AnnotationResource(annotation)
      $rootScope.$emit('beforeAnnotationCreated', annotation)
      annotation

    deleteAnnotation: (annotation) ->
      annotation.$delete(id: annotation.id).then ->
        $rootScope.$emit('annotationDeleted', annotation)
        annotation
]
