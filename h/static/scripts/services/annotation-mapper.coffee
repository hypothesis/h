# Wraps the annotation store to trigger events for the CRUD actions
class AnnotationMapper
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
      setupAndLoadAnnotations(annotations)

    this.createAnnotation = (annotation) ->
      annotation = new store.AnnotationResource(annotation)
      $rootScope.$emit('beforeAnnotationCreated', annotation)
      annotation

    this.deleteAnnotation = (annotation) ->
      annotation.$delete(id: annotation.id).then ->
        $rootScope.$emit('annotationDeleted', annotation)
      annotation

    # From Annotator core.
    setupAndLoadAnnotations = (annotations) =>
      loader = (annList=[]) =>
        now = annList.splice(0,10)

        for n in now
          this.setupAnnotation(n)

        # If there are more to do, do them after a 10ms break (for browser
        # responsiveness).
        if annList.length > 0
          setTimeout((-> loader(annList)), 10)
        else
          $rootScope.$emit('annotationsLoaded', [clone])

      clone = annotations.slice()

      if annotations.length # Do we have to do something?
          setTimeout -> loader(annotations)
        else # no pending scan
          # We can start parsing them right away
          loader(annotations)
      this

angular.module('h').service('annotationMapper', AnnotationMapper)
