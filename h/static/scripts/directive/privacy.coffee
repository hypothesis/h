module.exports = ['localStorage', 'permissions', (localStorage, permissions) ->
  VISIBILITY_KEY ='hypothesis.visibility'
  VISIBILITY_PUBLIC = 'public'
  VISIBILITY_PRIVATE = 'private'

  link: (scope, elem, attrs, controller) ->
    return unless controller?

    getLevels = ->
      [
        {
           name: VISIBILITY_PUBLIC,
           text: scope.group.name,
           isPublic: scope.group.public,
        }
        {
          name: VISIBILITY_PRIVATE,
          text: 'Only Me',
          isPrivate: true,
        }
      ]

    getLevel = (name) ->
      for level in getLevels()
        if level.name == name
          return level
      undefined

    controller.$formatters.push (selectedPermissions) ->
      return unless selectedPermissions?

      if permissions.isPrivate(selectedPermissions)
        getLevel(VISIBILITY_PRIVATE)
      else
        getLevel(VISIBILITY_PUBLIC)

    controller.$parsers.push (privacy) ->
      return unless privacy?

      if privacy.name is VISIBILITY_PUBLIC
        newPermissions = permissions.public()
        newPermissions.read = [scope.group.id]
      else
        newPermissions = permissions.private()

      # Cannot change the $modelValue into a new object
      # Just update its properties
      for key,val of newPermissions
        controller.$modelValue[key] = val

      controller.$modelValue

    controller.$render = ->
      unless controller.$modelValue.read?.length
        name = localStorage.getItem VISIBILITY_KEY
        name ?= VISIBILITY_PUBLIC
        level = getLevel(name)
        controller.$setViewValue level

      scope.level = controller.$viewValue

    scope.setLevel = (level) ->
      localStorage.setItem VISIBILITY_KEY, level.name
      controller.$setViewValue level
      controller.$render()

    scope.$watch 'group', ->
      scope.levels = getLevels()
      level = getLevel(controller.$viewValue.name)
      controller.$setViewValue(level)
      controller.$render()

  require: '?ngModel'
  restrict: 'E'
  scope:
    level: '='
    group: '='
  templateUrl: 'privacy.html'
]
