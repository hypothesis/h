# Watch the UI state and update scope properties.
module.exports = class AnnotationUIController
  this.$inject = ['$rootScope', '$scope', 'annotationUI']
  constructor:   ( $rootScope,   $scope,   annotationUI ) ->
    $rootScope.$watch (-> annotationUI.selectedAnnotationMap), (map={}) ->
      count = Object.keys(map).length
      $scope.selectedAnnotationsCount = count

      if count
        $scope.selectedAnnotations = map
      else
        $scope.selectedAnnotations = null

    $rootScope.$watch (-> annotationUI.focusedAnnotationMap), (map={}) ->
      $scope.focusedAnnotations = map

    $rootScope.$on 'annotationDeleted', (event, annotation) ->
      annotationUI.removeSelectedAnnotation(annotation)
