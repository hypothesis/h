annotation = ['$filter', ($filter) ->
  compile: (tElement, tAttrs, transclude) ->
    # Adjust the ngModel directive to use the isolate scope binding.
    # The expression will be bound in the isolate as '$modelValue'.
    if tAttrs.ngModel
      tAttrs.$set '$modelValue', tAttrs.ngModel, false
      tAttrs.$set 'ngModel', '$modelValue', false

    post: (scope, iElement, iAttrs, controller) ->
      return unless controller

      # Publish the controller
      scope.model = controller

      # Format the annotation for display
      controller.$formatters.push (value) ->
        return unless angular.isObject value
        angular.extend {}, value,
          text: ($filter 'converter') (value.text or '')

      # Update the annotation with text from the view
      controller.$parsers.push (value) ->
        if value.text != scope.$modelValue.text
          angular.extend scope.$modelValue, text: value.text
        else
          scope.$modelValue
  controller: 'AnnotationController'
  priority: 100  # Must run before ngModel
  require: '?ngModel'
  restrict: 'C'
  scope:
    $modelValue: '='
  templateUrl: 'annotation.html'
]


recursive = ['$compile', ($compile) ->
  compile: (tElement, tAttrs, transclude) ->
    transclude = $compile tElement, (scope, cloneAttachFn) ->
      transclude scope, cloneAttachFn
    , 1000
    post: (scope, iElement, iAttrs, controller) ->
      transclude scope, (el) -> iElement.replaceWith el
  priority: 1000
  restrict: 'A'
  terminal: true
]


tabReveal = ['$parse', ($parse) ->
  compile: (tElement, tAttrs, transclude) ->
    panes = []

    pre: (scope, iElement, iAttrs, [ngModel, tabbable] = controller) ->
      # Hijack the tabbable controller's addPane so that the visibility of the
      # secret ones can be managed. This avoids traversing the DOM to find
      # the tab panes.
      addPane = tabbable.addPane
      tabbable.addPane = (element, attr) =>
        removePane = addPane.call tabbable, element, attr
        panes.push
          element: element
          attr: attr
        =>
          for i in [0..panes.length]
            if panes[i].element is element
              panes.splice i, 1
              break
          removePane()

    post: (scope, iElement, iAttrs, [ngModel, tabbable] = controller) ->
      tabs = angular.element(iElement.children()[0]).find('li')
      hiddenPanes = ($parse iAttrs.tabReveal)()
      unless angular.isArray hiddenPanes
        throw (new TypeError 'tabReveal expression must evaluate to an Array')

      update = =>
        for i in [0..panes.length-1]
          pane = panes[i]
          value = pane.attr.value || pane.attr.title
          if value == ngModel.$modelValue
            deform.focusFirstInput pane.element
            pane.element.css 'display', ''
            angular.element(tabs[i]).css 'display', ''
          else if value in hiddenPanes
            pane.element.css 'display', 'none'
            angular.element(tabs[i]).css 'display', 'none'

      scope.$watch iAttrs.ngModel, => scope.$evalAsync update
  require: ['ngModel', 'tabbable']
]



writer = ['$filter', ($filter) ->
  compile: (tElement, tAttrs, transclude) ->
    post: (scope, iElement, iAttrs, [annotation, controller]) ->
      scope.editing = true

      scope.$watch 'editText', (newValue) ->
        if scope.form.$valid
          controller.$viewValue.text = scope.editText
          controller.$setViewValue controller.$viewValue
          #scope.previewText = ($filter 'converter') scope.editText
        else
          scope.previewText = ''
  require: ['annotation', '^ngModel']
  restrict: 'C'
]


angular.module('h.directives', ['ngSanitize', 'deform'])
  .directive('annotation', annotation)
  .directive('recursive', recursive)
  .directive('tabReveal', tabReveal)
  .directive('writer', writer)
