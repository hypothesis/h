# Wraps the annotation store to trigger events for the CRUD actions
module.exports = [
  '$rootScope', 'threading', 'store',
  ($rootScope, threading, store) ->
    setupAnnotation: (ann) -> ann

    ###*
    # @ngdoc function
    #
    # @name annotationMapper.loadAnnotations
    #
    # @description Load some annotations and replies into the current page
    #   context.
    #
    # @param {array} annotations The array of annotation objects to load.
    # @param {array} replies An array of all replies to the given annotations.
    #
    # @returns nothing
    #
    ###
    loadAnnotations: (annotations, replies=[]) ->
      # Pass both the annotations and all of the replies to those annotations
      # into the threading code as one concatenated list. The threading code
      # will arrange these into nested threads for display.
      annotations = annotations.concat(replies)

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
