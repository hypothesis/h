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

      scope.auth = {}
      scope.auth.delete =
        if scope.model.$modelValue? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'delete', scope.model.$modelValue
        else
          true
      scope.auth.update =
        if scope.model.$modelValue? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'update', scope.model.$modelValue
        else
          true

    # Publish the controller
    scope.model = controller

  controller: 'AnnotationController'
  priority: 100  # Must run before ngModel
  require: '?ngModel'
  restrict: 'C'
  scope:
    mode: '@'
    replies: '@'
  templateUrl: 'annotation.html'
]

angular.module('h.app_directives', ['ngSanitize'])
  .directive('annotation', annotation)
