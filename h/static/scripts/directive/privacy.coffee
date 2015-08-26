module.exports = ['localStorage', 'permissions', (localStorage, permissions) ->
  VISIBILITY_KEY ='hypothesis.visibility'
  VISIBILITY_PUBLIC = 'public'
  VISIBILITY_PRIVATE = 'private'


  isPublic  = (level) -> level == VISIBILITY_PUBLIC

  link: (scope, elem, attrs, controller) ->
    return unless controller?

    getLevels = ->
      [
        {
           name: VISIBILITY_PUBLIC,
           text: scope.group().name,
           isGroup: scope.group().hashid != '__world__'
        }
        {name: VISIBILITY_PRIVATE, text: 'Only Me'}
      ]

    getLevel = (name) ->
      for level in getLevels()
        if level.name == name
          return level
      undefined

    controller.$formatters.push (selectedPermissions) ->
      return unless selectedPermissions?

      if permissions.isPublic(selectedPermissions)
        getLevel(VISIBILITY_PUBLIC)
      else
        getLevel(VISIBILITY_PRIVATE)

    controller.$parsers.push (privacy) ->
      return unless privacy?

      if isPublic(privacy.name)
        newPermissions = permissions.public()
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

    scope.levels = getLevels()
    scope.setLevel = (level) ->
      localStorage.setItem VISIBILITY_KEY, level.name
      controller.$setViewValue level
      controller.$render()
    scope.isPublic = isPublic

  require: '?ngModel'
  restrict: 'E'
  scope:
    level: '='
    group: '&'
  templateUrl: 'privacy.html'
]
