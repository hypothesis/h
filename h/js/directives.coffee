navTabsDirective = (deform) ->
  link: (scope, iElement, iAttrs, controller) ->
    iElement.find('a')

    # Focus the first form element when showing a tab pane
      .on 'shown', (e) ->
        target = $(e.target).data('target')
        deform.focusFirstInput(target)

    # Always show the first pane to start
    .first().tab('show')
  restrict: 'C'
navTabsDirective.$inject = ['deform']

angular.module('h.directives', ['ngSanitize', 'deform'])
  .directive('navTabs', navTabsDirective)
