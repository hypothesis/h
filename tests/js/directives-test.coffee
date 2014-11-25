assert = chai.assert

describe 'h.directives', ->
  $scope = null
  $compile = null
  $injector = null
  fakeWindow = null

  beforeEach module ($provide, $filterProvider) ->
    fakeWindow = {open: sinon.spy()}
    fakeDocument = angular.element({
      createElement: (tag) -> document.createElement(tag)
      baseURI: 'http://example.com'
    })

    $provide.value('$window', fakeWindow)
    $provide.value('$document', fakeDocument)

    $filterProvider.register 'persona', ->
      (user, part) ->
        parts = user.slice(5).split('@')
        {username: parts[0], provider: parts[1]}[part]

    return

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach inject (_$compile_, _$rootScope_, _$injector_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()
    $injector = _$injector_

  describe '.formValidate', ->
    $element = null

    beforeEach ->
      $scope.model = {username: undefined}

      template = '''
      <form form-validate name="login" onsubmit="return false">
        <div class="form-field">
          <input type="text" class="form-input" name="username"
                 ng-model="model.username" name="username"
                 required ng-minlength="3" />
        </div>
      </form>
      '''

      $element = $compile(angular.element(template))($scope)
      $scope.$digest()

    it 'should remove an error class to an valid field on change', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]').addClass('form-field-error')

      $input.controller('ngModel').$setViewValue('abc')
      $scope.$digest()

      assert.notInclude($field.prop('className'), 'form-field-error')
      assert.notInclude($input.prop('className'), 'form-field-error')

    it 'should apply an error class to an invalid field on submit', ->
      $field = $element.find('.form-field')
      $element.triggerHandler('submit')
      assert.include($field.prop('className'), 'form-field-error')

    it 'should remove an error class from a valid field on submit', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]')
      $input.val('abc').triggerHandler('input')

      $element.triggerHandler('submit')
      assert.notInclude($field.prop('className'), 'form-field-error')

    it 'should apply an error class if the form recieves errors after a submit action', ->
      $element.trigger('submit')
      $element.controller('form').username.$setValidity('response', false)

      $field = $element.find('.form-field')
      assert.include $field.prop('className'), 'form-field-error'

    it 'should remove an error class on valid input when the view model changes', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]')
      $input.val('abc').triggerHandler('input')

      assert.notInclude($field.prop('className'), 'form-field-error')

    it 'should not add an error class on invalid input on when the view changes', ->
      $field = $element.find('.form-field')
      $input = $element.find('[name=username]')
      $input.val('ab').triggerHandler('input')

      assert.notInclude($field.prop('className'), 'form-field-error')

    it 'should reset the "response" error when the view changes', ->
      $field = $element.find('.form-field')
      $input = $element.find('[name=username]')
      controller = $input.controller('ngModel')
      controller.$setViewValue('abc')

      # Submit Event
      $element.triggerHandler('submit')
      controller.$setValidity('response', false)
      controller.responseErrorMessage = 'fail'
      $scope.$digest()

      assert.include($field.prop('className'), 'form-field-error', 'Fail fast check')

      controller.$setViewValue('abc')
      $scope.$digest()

      assert.notInclude($field.prop('className'), 'form-field-error')

    it 'should hide errors if the model is marked as pristine', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]')
      controller = $input.controller('ngModel')

      # Submit Event
      $element.triggerHandler('submit')
      controller.$setValidity('response', false)
      controller.responseErrorMessage = 'fail'
      $scope.$digest()

      assert.include($field.prop('className'), 'form-field-error', 'Fail fast check')

      # Then clear it out and mark it as pristine
      controller.$setPristine()
      $scope.$digest()

      assert.notInclude($field.prop('className'), 'form-field-error')


  describe '.match', ->
    $element = null
    $isolateScope = null

    beforeEach ->
      $scope.model = {a: 1, b: 1}

      $element = $compile('<input name="confirmation" ng-model="model.b" match="model.a" />')($scope)
      $isolateScope = $element.isolateScope()
      $scope.$digest()

    it 'is valid if both properties have the same value', ->
      controller = $element.controller('ngModel')
      assert.isFalse(controller.$error.match)

    it 'is invalid if the local property differs', ->
      $isolateScope.match = 2
      $isolateScope.$digest()

      controller = $element.controller('ngModel')
      assert.isTrue(controller.$error.match)

    it 'is invalid if the matched property differs', ->
      $scope.model.a = 2
      $scope.$digest()

      controller = $element.controller('ngModel')
      assert.isTrue(controller.$error.match)

    it 'is invalid if the input itself is changed', ->
      $element.val('2').trigger('input').keyup()
      $scope.$digest()

      controller = $element.controller('ngModel')
      assert.isTrue(controller.$error.match)


  describe '.privacy', ->
    $element = null
    $isolateScope = null
    modelCtrl = null
    settings = null

    beforeEach ->
      $scope.permissions = {read: ['acct:user@example.com']}
      settings = $injector.get('DSCacheFactory').createCache('ui-settings')

    afterEach ->
      $injector.get('DSCacheFactory').clearAll()

    it 'initializes the default privacy to "Only Me"', ->
      $element = $compile('<privacy ng-model="permissions">')($scope)
      $scope.$digest()
      assert.equal(settings.get('privacy'), 'Only Me')

    it 'stores the default privacy level when it changes', ->
      $element = $compile('<privacy ng-model="permissions">')($scope)
      $scope.$digest()
      $isolateScope = $element.isolateScope()
      $isolateScope.setLevel('Public')
      assert.equal(settings.get('privacy'), 'Public')

    describe 'when privacy-default attribute is absent', ->
      beforeEach ->
        settings.put('privacy', 'Public')
        $element = $compile('<privacy ng-model="permissions">')($scope)
        $scope.$digest()
        $isolateScope = $element.isolateScope()

      it 'sets the initial permissions based on the stored privacy level', ->
        assert.equal($isolateScope.level, 'Public')

      it 'does not alter the level on subsequent renderings', ->
        modelCtrl = $element.controller('ngModel')
        settings.put('privacy', 'Only Me')
        $scope.permissions.read = ['acct:user@example.com']
        $scope.$digest()
        assert.equal($isolateScope.level, 'Public')

    describe 'when privacy-default attribute is present', ->
      it 'does not alter the level if the value is "false"', ->
        $element = $compile('<privacy ng-model="permissions" privacy-default="false">')($scope)
        $scope.permissions.read = ['group:__world__']
        $scope.$digest()
        $isolateScope = $element.isolateScope()
        assert.equal($isolateScope.level, 'Public')

      it 'alters the level if the value is not "false"', ->
        $element = $compile('<privacy ng-model="permissions" privacy-default>')($scope)
        $scope.permissions.read = ['group:__world__']
        $scope.$digest()
        $isolateScope = $element.isolateScope()
        $isolateScope.level = 'Public'
