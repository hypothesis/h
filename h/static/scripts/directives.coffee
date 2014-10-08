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


angular.module('h')
.directive('privacy', privacy)
.directive('repeatAnim', repeatAnim)
.directive('whenscrolled', whenscrolled)
.directive('match', match)
