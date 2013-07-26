annotation = ['$filter', 'annotator', ($filter, annotator) ->
  link: (scope, elem, attrs, controller) ->
    return unless controller?

    # Bind shift+enter to save
    elem.bind
      keydown: (e) ->
        if e.keyCode == 13 && e.shiftKey
          e.preventDefault()
          scope.save()

    # Watch for changes
    scope.$watch 'model.$modelValue.id', (id) ->
      scope.thread = annotator.threading.idTable[id]

    # Publish the controller
    scope.model = controller
  controller: 'AnnotationController'
  priority: 100  # Must run before ngModel
  require: '?ngModel'
  restrict: 'C'
  scope: {}
  templateUrl: 'annotation.html'
]

angular.module('h.app_directives', ['ngSanitize'])
  .directive('annotation', annotation)
