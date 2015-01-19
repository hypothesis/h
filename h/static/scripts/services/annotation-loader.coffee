class AnnotationLoader
  this.$inject = ['$rootScope', 'threading', 'store']
  constructor: ($rootScope, threading, store) ->
    @rootScope = $rootScope
    @threading = threading
    @store = store

  setupAnnotation: (ann) -> ann

  loadAnnotations: (annotations) ->
    annotations = for annotation in annotations
      container = @threading.idTable[annotation.id]
      if container?.message
        angular.copy(annotation, container.message)
        @rootScope.$emit('annotationUpdated', container.message)
        continue
      else
        annotation
    this._setupAndLoadAnnotations(new @store.AnnotationResource(a) for a in annotations)

  # From Annotator core.
  _setupAndLoadAnnotations: (annotations) ->
    loader = (annList=[]) =>
      now = annList.splice(0,10)

      for n in now
        this.setupAnnotation(n)

      # If there are more to do, do them after a 10ms break (for browser
      # responsiveness).
      if annList.length > 0
        setTimeout((-> loader(annList)), 10)
      else
        @rootScope.$emit('annotationsLoaded', [clone])

    clone = annotations.slice()

    if annotations.length # Do we have to do something?
        setTimeout -> loader(annotations)
      else # no pending scan
        # We can start parsing them right away
        loader(annotations)
    this

angular.module('h').service('annotationLoader', AnnotationLoader)
