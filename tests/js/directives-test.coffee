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
    })

    $provide.value('$window', fakeWindow)
    $provide.value('$document', fakeDocument)

    $filterProvider.register 'persona', ->
      (user, part) ->
        parts = user.slice(5).split('@')
        {username: parts[0], provider: parts[1]}[part]

    return

  beforeEach module('h.templates')
  beforeEach module('h.directives')

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

  describe '.showAccount', ->
    $element = null

    beforeEach ->
      $element = $compile('<a show-account>Account</a>')($scope)
      $scope.$digest()

    it 'triggers the "nav:account" event when the Account item is clicked', (done) ->
      $scope.$on 'nav:account', ->
        done()
      $element.click()
