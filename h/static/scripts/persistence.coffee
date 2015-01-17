class Persistence
  #this.$inject = ['$rootScope']
  constructor:   ( $rootScope, @annotator ) ->
    $rootScope.$on 'beforeAnnotationCreated', (event, annotation) =>
      console.log 'beforeAnnotationCreated!'
      @annotator.publish 'beforeAnnotationCreated', annotation

    $rootScope.$on 'annotationCreated', (event, annotation) =>
      console.log 'annotationCreated!'
      @annotator.publish 'annotationCreated', annotation

    $rootScope.$on 'annotationUpdated', (event, annotation) =>
      console.log 'annotationUpdated!'
      @annotator.publish('annotationUpdated', [annotation])

    $rootScope.$on 'beforeAnnotationUpdated', (event, annotation) =>
      console.log 'beforeAnnotationUpdated!'
      @annotator.publish('beforeAnnotationUpdated', [annotation])

    $rootScope.$on 'annotationDeleted', (event, annotation) =>
      console.log 'annotationDeleted!'
      @annotator.deleteAnnotation annotation

    $rootScope.$on 'loadAnnotations', (event, annotations) =>
      console.log 'loadAnnotations!'
      @annotator.loadAnnotations annotations

