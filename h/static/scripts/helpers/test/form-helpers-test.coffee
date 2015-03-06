{module, inject} = require('angular-mock')

assert = chai.assert
angular = require('angular')



describe 'h.helpers:form-helpers', ->
  $compile = null
  $scope = null
  formHelpers = null

  before ->
    angular.module('h.helpers', [])
    require('../form-helpers')

  beforeEach module('h.helpers')

  beforeEach inject (_$compile_, _$rootScope_, _formHelpers_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()
    formHelpers = _formHelpers_

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

  describe '.applyValidationErrors', ->
    form = null

    beforeEach ->
      form =
        $setValidity: sinon.spy()
        username: {$setValidity: sinon.spy()}
        password: {$setValidity: sinon.spy()}

    it 'sets the "response" error key for each field with errors', ->
      formHelpers.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.calledWith(form.username.$setValidity, 'response', false)
      assert.calledWith(form.password.$setValidity, 'response', false)

    it 'adds an error message to each input controller', ->
      formHelpers.applyValidationErrors form,
        username: 'must be at least 3 characters'
        password: 'must be present'

      assert.equal(form.username.responseErrorMessage, 'must be at least 3 characters')
      assert.equal(form.password.responseErrorMessage, 'must be present')

    it 'sets the "response" error key if the form has a failure reason', ->
      formHelpers.applyValidationErrors form, null, 'fail'
      assert.calledWith(form.$setValidity, 'response', false)

    it 'adds an reason message as the response error', ->
      formHelpers.applyValidationErrors form, null, 'fail'
      assert.equal(form.responseErrorMessage, 'fail')
