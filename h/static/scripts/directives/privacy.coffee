privacy = ['$window', ($window) ->
  VISIBILITY_KEY ='hypothesis.visibility'
  VISIBILITY_PUBLIC = 'public'
  VISIBILITY_PRIVATE = 'private'
  # Detection is needed because we run often as a third party widget and
  # third party storage blocking often blocks cookies and local storage
  # https://github.com/Modernizr/Modernizr/blob/master/feature-detects/storage/localstorage.js
  storage = do ->
    key = 'hypothesis.testKey'
    try
      $window.localStorage.setItem  key, key
      $window.localStorage.removeItem key
      $window.localStorage
    catch
      memoryStorage = {}
      getItem: (key) ->
        if key of memoryStorage then memoryStorage[key] else null
      setItem: (key, value) ->
        memoryStorage[key] = value

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
          permissions.read = ['group:__world__']
      else
          permissions.read = [attrs.user]

      permissions.update = [attrs.user]
      permissions.delete = [attrs.user]
      permissions.admin = [attrs.user]

      permissions

    controller.$render = ->
      unless controller.$modelValue.read.length
        visibility = storage.getItem VISIBILITY_KEY
        level = if visibility is VISIBILITY_PUBLIC
          'Public'
        else
          'Only Me'
        controller.$setViewValue level

      scope.level = controller.$viewValue

    scope.levels = levels
    scope.setLevel = (level) ->
      visibility = if level is 'Public'
          VISIBILITY_PUBLIC
        else
          VISIBILITY_PRIVATE
      storage.setItem VISIBILITY_KEY, visibility
      controller.$setViewValue level
      controller.$render()
  require: '?ngModel'
  restrict: 'E'
  scope: {}
  templateUrl: 'privacy.html'
]

angular.module('h')
.directive('privacy', privacy)
