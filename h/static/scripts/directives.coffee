imports = [
  'ngSanitize'
  'ngTagsInput'
  'h.helpers.documentHelpers'
  'h.services'
]


formInput = ->
  link: (scope, elem, attr, [form, model, validator]) ->
    return unless form?.$name and model?.$name and validator

    fieldClassName = 'form-field'
    errorClassName = 'form-field-error'

    render = model.$render

    resetResponse = (value) ->
      model.$setValidity('response', true)
      value

    toggleClass = (addClass) ->
      elem.toggleClass(errorClassName, addClass)
      elem.parent().toggleClass(errorClassName, addClass)

    model.$parsers.unshift(resetResponse)
    model.$render = ->
      toggleClass(model.$invalid and model.$dirty)
      render()

    validator.addControl(model)
    scope.$on '$destroy', -> validator.removeControl this

    scope.$watch ->
      if model.$modelValue? or model.$pristine
        model.$render()
      return

  require: ['^?form', '?ngModel', '^?formValidate']
  restrict: 'C'


formValidate = ->
  controller: ->
    controls = {}

    addControl: (control) ->
      if control.$name
        controls[control.$name] = control

    removeControl: (control) ->
      if control.$name
        delete controls[control.$name]

    submit: ->
      # make all the controls dirty and re-render them
      for _, control of controls
        control.$setViewValue(control.$viewValue)
        control.$render()

  link: (scope, elem, attr, ctrl) ->
    elem.on 'submit', ->
      ctrl.submit()


privacy = ->
  levels = ['Public', 'Only Me']

  link: (scope, elem, attrs, controller) ->
    return unless controller?

    controller.$formatters.push (permissions) ->
      return unless permissions?

      if 'group:__world__' in (permissions.read or [])
        'Public'
      else
        'Only Me'

    controller.$parsers.push (privacy) ->
      return unless privacy?

      permissions = controller.$modelValue
      if privacy is 'Public'
        if permissions.read
          unless 'group:__world__' in permissions.read
            permissions.read.push 'group:__world__'
        else
          permissions.read = ['group:__world__']
      else
        read = permissions.read or []
        read = (role for role in read when role isnt 'group:__world__')
        permissions.read = read

      permissions

    controller.$render = ->
      scope.level = controller.$viewValue

    scope.levels = levels
    scope.setLevel = (level) ->
      controller.$setViewValue level
      controller.$render()
  require: '?ngModel'
  restrict: 'E'
  scope: {}
  templateUrl: 'privacy.html'


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


# TODO: Move this behaviour to a route.
showAccount = ->
  restrict: 'A'
  link: (scope, elem, attr) ->
    elem.on 'click', (event) ->
      event.preventDefault()
      scope.$emit('nav:account')


repeatAnim = ->
  restrict: 'A'
  scope:
    array: '='
  template: '<div ng-init="runAnimOnLast()"><div ng-transclude></div></div>'
  transclude: true

  controller: ($scope, $element, $attrs) ->
    $scope.runAnimOnLast = ->
      #Run anim on the item's element
      #(which will be last child of directive element)
      item=$scope.array[0]
      itemElm = jQuery($element)
        .children()
        .first()
        .children()

      unless item._anim?
        return
      if item._anim is 'fade'
        itemElm
          .css({ opacity: 0 })
          .animate({ opacity: 1 }, 1500)
      else
        if item._anim is 'slide'
          itemElm
            .css({ 'margin-left': itemElm.width() })
            .animate({ 'margin-left': '0px' }, 1500)
      return


whenscrolled = ->
  link: (scope, elem, attr) ->
    elem.bind 'scroll', ->
      {clientHeight, scrollHeight, scrollTop} = elem[0]
      if scrollHeight - scrollTop <= clientHeight + 40
        scope.$apply attr.whenscrolled

match = ->
  link: (scope, elem, attr, input) ->
    validate = ->
      scope.$evalAsync ->
        input.$setValidity('match', scope.match == input.$modelValue)

    elem.on('keyup', validate)
    scope.$watch('match', validate)
  scope:
    match: '='
  restrict: 'A'
  require: 'ngModel'


angular.module('h.directives', imports)
.directive('formInput', formInput)
.directive('formValidate', formValidate)
.directive('privacy', privacy)
.directive('tabReveal', tabReveal)
.directive('showAccount', showAccount)
.directive('repeatAnim', repeatAnim)
.directive('whenscrolled', whenscrolled)
.directive('match', match)
