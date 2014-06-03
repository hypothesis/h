annotation = ['$filter', 'annotator', ($filter, annotator) ->
  link: (scope, elem, attrs, controller) ->
    return unless controller?

    # Bind shift+enter to save
    elem.bind
      keydown: (e) ->
        if e.keyCode == 13 && e.shiftKey
          scope.save(e)

    # Watch for changes
    scope.$watch 'model', (model) ->
      scope.thread = annotator.threading.idTable[model.id]

      scope.auth = {}
      scope.auth.delete =
        if model? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'delete', model
        else
          true
      scope.auth.update =
        if scope.model? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'update', model
        else
          true

  controller: 'AnnotationController'
  require: '?ngModel'
  restrict: 'C'
  scope:
    model: '=ngModel'
    mode: '@'
    replies: '@'
  templateUrl: 'annotation.html'
]

angular.module('h.app_directives', ['ngSanitize'])
.directive('annotation', annotation)
