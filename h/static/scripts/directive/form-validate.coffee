module.exports = ->
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
