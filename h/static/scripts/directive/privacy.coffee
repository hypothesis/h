module.exports = ['localStorage', 'permissions', (localStorage, permissions) ->
  VISIBILITY_KEY ='hypothesis.visibility'
  VISIBILITY_PUBLIC = 'public'
  VISIBILITY_PRIVATE = 'private'

  levels = [
    {name: VISIBILITY_PUBLIC, text: 'Public'}
    {name: VISIBILITY_PRIVATE, text: 'Only Me'}
  ]

  getLevel = (name) ->
    for level in levels
      if level.name == name
        return level
    undefined

  isPublic  = (level) -> level == VISIBILITY_PUBLIC

  link: (scope, elem, attrs, controller) ->
    return unless controller?

    controller.$formatters.push (value) ->
      if value?.read?.length
        if permissions.isPublic(value)
          return getLevel(VISIBILITY_PUBLIC)
        else
          return getLevel(VISIBILITY_PRIVATE)
      else
        return undefined

    controller.$parsers.push (value) ->
      if isPublic(value.name)
        return permissions.public()
      else
        return permissions.private()

    controller.$render = ->
      if controller.$viewValue?
        scope.level = controller.$viewValue
      else
        name = localStorage.getItem(VISIBILITY_KEY)
        level = getLevel(name ? VISIBILITY_PUBLIC)
        scope.setLevel(level)

    scope.levels = levels

    scope.setLevel = (level) ->
      localStorage.setItem(VISIBILITY_KEY, level.name)
      controller.$setViewValue(level)
      controller.$render()

    scope.isPublic = isPublic

  require: '?ngModel'
  restrict: 'E'
  scope: {}
  templateUrl: 'privacy.html'
]
