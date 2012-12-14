annotation = ['$filter', ($filter) ->
  compile: (tElement, tAttrs, transclude) ->
    # adjust ng-model for isolate scope
    if tAttrs.ngModel
      tAttrs.$set 'model', tAttrs.ngModel, false
      tAttrs.$set 'ngModel', 'model', false
    post: (scope, iElement, iAttrs, controller) ->
      controller.$formatters.push (value) ->
        return unless angular.isObject value
        angular.extend {}, value,
          text: ($filter 'converter') value.text
          created: ($filter 'fuzzyTime') value.created
          updated: ($filter 'fuzzyTime') value.updated
          user: ($filter 'userName') value.user

      controller.$render = ->
        scope.$viewValue = controller.$viewValue
  controller: 'AnnotationController'
  priority: 100
  require: '^ngModel'
  restrict: 'C'
  scope:
    model: '='
  templateUrl: 'annotation.html'
]


recursive = ['$compile', ($compile) ->
  compile: (tElement, tAttrs) ->
    linkRec = $compile tElement.contents().remove(), (scope, cloneAttachFn) ->
      linkRec scope, cloneAttachFn
    post: (scope, iElement, iAttrs, controller) ->
      linkRec scope, (contents) -> iElement.append contents
  restrict: 'A'
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
angular.module('h.directives', ['ngSanitize', 'deform'])
  .directive('annotation', annotation)
  .directive('recursive', recursive)
  .directive('tabReveal', tabReveal)
