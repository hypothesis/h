# Extend deform to allow targeting focusing of input when multiple forms
# are on the same page. See https://github.com/Pylons/deform/pull/128
angular.extend deform,
  focusFirstInput: (el) ->
    el = el || document.body
    input = $(el).find(':input')
      .filter('[id ^= deformField]')
      .filter('[type != hidden]')
      .first()
    raw = input?.get(0)
    if raw?.type in ['text', 'file', 'password', 'textarea']
      if raw.className != "hasDatepicker" then input.focus()


# AngularJS directive that creates data bindings for named controls on forms
# with the 'deform' class and triggers deform callbacks during linking.
deformDirective = ->
  compile: (tElement, tAttrs, transclude) ->
    # Capture the initial values from the server-side render and set a model
    # binding for all the named controls.
    initValues = {}
    $controls = tElement.find('input,select,textarea').filter('[name]')
      .filter ->
        # Ignore private members (like __formid__) and hidden fields
        # (angular does not data-bind hidden fields)
        not (this.name.match '^_' or this.type is hidden)
      .each ->
        initValues[this.name] =
          if this.tagName == 'select'
            options = []
            selected = null
            $(this)
              .attr(
                'data-ng-options',
                "value for value in #{this.name}.values"
              )
              .find('option').filter('[value!=""]')
              .each (i) ->
                if this.selected then selected = i
                options.push
                  label: this.label or this.innerText
                  value: this.value
              .remove()
            options: options
            selected: selected
          else
            this.value
        $(this).attr 'data-ng-model', "#{this.name}"

    # Link function
    (scope, iElement, iAttrs, controller) ->
      if scope.addForm?
        name = iAttrs.name or iAttrs.ngModel or iAttrs.id
        scope.addForm iElement, name
      deform.processCallbacks()
  restrict: 'C'
  require: 'form'
  scope: false


angular.module('deform', []).config [
  '$provide', '$compileProvider', '$filterProvider',
  ($provide, $compileProvider, $filterProvider) ->
    # Process any pending callbacks from the initial load
    deform.processCallbacks()
    # Register the deform service and directive
    $provide.value 'deform', deform
    $compileProvider.directive 'deform', deformDirective
]
