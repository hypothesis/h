annotation = ['$filter', ($filter) ->
  compile: (tElement, tAttrs, transclude) ->
    # Adjust the ngModel directive to use the isolate scope binding.
    # The expression will be bound in the isolate as '$modelValue'.
    if tAttrs.ngModel
      tAttrs.$set '$modelValue', tAttrs.ngModel, false
      tAttrs.$set 'ngModel', '$modelValue', false

    post: (scope, iElement, iAttrs, controller) ->
      return unless controller

      # Bind shift+enter to save
      iElement.find('textarea').bind
        keydown: (e) ->
          if e.keyCode == 13 && e.shiftKey
            e.preventDefault()
            scope.save()

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

      scope.$watch 'editText', (newValue) ->
        if scope.form.$valid
          controller.$viewValue.text = scope.editText
          controller.$setViewValue controller.$viewValue
          #scope.previewText = ($filter 'converter') scope.editText
        else
          scope.previewText = ''

      # Publish the controller
      scope.model = controller
  controller: 'AnnotationController'
  priority: 100  # Must run before ngModel
  require: '?ngModel'
  restrict: 'C'
  scope:
    $modelValue: '='
  templateUrl: 'annotation.html'
]


recursive = ['$compile', '$timeout', ($compile, $timeout) ->
  compile: (tElement, tAttrs, transclude) ->
    placeholder = angular.element '<!-- recursive -->'
    attachQueue = []
    tick = false

    template = tElement.contents().clone()
    tElement.html ''

    transclude = $compile template, (scope, cloneAttachFn) ->
      clone = placeholder.clone()
      cloneAttachFn clone
      $timeout ->
        transclude scope, (el, scope) -> attachQueue.push [clone, el]
        unless tick
          tick = true
          requestAnimationFrame ->
            tick = false
            for [clone, el] in attachQueue
              clone.replaceWith el
            attachQueue = []
      clone
    post: (scope, iElement, iAttrs, controller) ->
      transclude scope, (contents) -> iElement.append contents
  restrict: 'A'
  terminal: true
]


resettable = ->
  compile: (tElement, tAttrs, transclude) ->
    post: (scope, iElement, iAttrs) ->
      reset = ->
        transclude scope, (el) ->
          iElement.replaceWith el
          iElement = el
      reset()
      scope.$on '$reset', reset
  priority: 5000
  restrict: 'A'
  transclude: 'element'


tabReveal = ['$parse', ($parse) ->
  compile: (tElement, tAttrs, transclude) ->
    panes = []
    hiddenPanesGet = $parse tAttrs.tabReveal

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
      tabs = angular.element(iElement.children()[0].childNodes)
      render = angular.bind ngModel, ngModel.$render

      ngModel.$render = ->
        render()
        hiddenPanes = hiddenPanesGet scope
        return unless angular.isArray hiddenPanes

        for i in [0..panes.length-1]
          pane = panes[i]
          value = pane.attr.value || pane.attr.title
          if value == ngModel.$viewValue
            pane.element.css 'display', ''
            angular.element(tabs[i]).css 'display', ''
          else if value in hiddenPanes
            pane.element.css 'display', 'none'
            angular.element(tabs[i]).css 'display', 'none'
  require: ['ngModel', 'tabbable']
]


thread = ->
  link: (scope, iElement, iAttrs, controller) ->
    scope.collapsed = false
  restrict: 'C'
  scope: true


angular.module('h.directives', ['ngSanitize'])
  .directive('annotation', annotation)
  .directive('recursive', recursive)
  .directive('resettable', resettable)
  .directive('tabReveal', tabReveal)
  .directive('thread', thread)
