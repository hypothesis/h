# Wraps the annotation store to trigger events for the CRUD actions
class AnnotationMapperService
  this.$inject = ['$rootScope', 'threading', 'store']
  constructor: ($rootScope, threading, store) ->
    this.setupAnnotation = (ann) -> ann

    this.loadAnnotations = (annotations) ->
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

    this.createAnnotation = (annotation) ->
      annotation = new store.AnnotationResource(annotation)
      $rootScope.$emit('beforeAnnotationCreated', annotation)
      annotation

    this.deleteAnnotation = (annotation) ->
      annotation.$delete(id: annotation.id).then ->
        $rootScope.$emit('annotationDeleted', annotation)
      annotation

angular.module('h').service('annotationMapper', AnnotationMapperService)
