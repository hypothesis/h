annotation = ['$filter', 'annotator', ($filter, annotator) ->
  link: (scope, elem, attrs, controller) ->
    return unless controller?

    # Bind shift+enter to save
    elem.bind
      keydown: (e) ->
        if e.keyCode == 13 && e.shiftKey
          scope.save(e)

    scope.addTag = (tag) ->
      scope.model.tags ?= []
      scope.model.tags.push(tag.text)

    scope.removeTag = (tag) ->
      scope.model.tags = scope.model.tags.filter((t) -> t isnt tag.text)
      delete scope.model.tags if scope.model.tags.length is 0

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

      scope.tags = ({text: tag} for tag in scope.model.tags or [])

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
