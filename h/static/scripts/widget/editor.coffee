imports = [
  'h.annotation'
  'h.services'
  'h.widget.head'
]


class Editor
  this.$inject = [
    '$location', '$routeParams', '$sce', '$scope',
    'annotator', 'head'
  ]
  constructor: (
     $location,   $routeParams,   $sce,   $scope,
     annotator,   head
  ) ->
    save = (annotation) ->
      $location.path('/view').replace()
      delete annotator.ongoingEdit
      head.focusAnnotation annotation
      for c in head.clients
        c.notify method: 'onEditorSubmit'
        c.notify method: 'onEditorHide'

    cancel = (annotation) ->
      $location.path('/view').replace()
      delete annotator.ongoingEdit
      for c in head.clients
        c.notify method: 'onEditorHide'

    annotator.subscribe 'annotationCreated', save
    annotator.subscribe 'annotationDeleted', cancel

    $scope.$on '$destroy', ->
      annotator.unsubscribe 'annotationCreated', save
      annotator.unsubscribe 'annotationDeleted', cancel

    $scope.$watch 'annotation.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false

    $scope.annotation = annotator.ongoingEdit

angular.module('h.widget.editor', imports)
.controller('EditorController', Editor)
