{module, inject} = angular.mock

describe 'form-input', ->
  $compile = null
  $field = null
  $scope = null

  before ->
    angular.module('h', ['ng'])
    .directive('formInput', require('../form-input'))

  beforeEach module('h')
  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  beforeEach ->
    $scope.model = {username: undefined}

    template = '''
      <div class="form-field">
        <input type="text" class="form-input" name="username"
               ng-model="model.username" name="username"
               required ng-minlength="3" />
      </div>
    '''

    $field = $compile(angular.element(template))($scope)
    $scope.$digest()

  it 'should remove an error class to an valid field on change', ->
    $field.addClass('form-field-error')
    $input = $field.find('[name=username]').addClass('form-field-error')

    $input.controller('ngModel').$setViewValue('abc')
    $scope.$digest()

    assert.notInclude($field.prop('className'), 'form-field-error')
    assert.notInclude($input.prop('className'), 'form-field-error')

  it 'should apply an error class to an invalid field on render', ->
    $input = $field.find('[name=username]')

    $input.triggerHandler('input')  # set dirty
    $input.controller('ngModel').$render()

    assert.include($field.prop('className'), 'form-field-error')

  it 'should remove an error class from a valid field on render', ->
    $field.addClass('form-field-error')
    $input = $field.find('[name=username]')

    $input.val('abc').triggerHandler('input')
    $input.controller('ngModel').$render()

    assert.notInclude($field.prop('className'), 'form-field-error')

  it 'should remove an error class on valid input', ->
    $field.addClass('form-field-error')
    $input = $field.find('[name=username]')

    $input.val('abc').triggerHandler('input')

    assert.notInclude($field.prop('className'), 'form-field-error')

  it 'should not add an error class on invalid input', ->
    $input = $field.find('[name=username]')
    $input.val('ab').triggerHandler('input')

    assert.notInclude($field.prop('className'), 'form-field-error')

  it 'should reset the "response" error when the view changes', ->
    $input = $field.find('[name=username]')
    controller = $input.controller('ngModel')

    controller.$setViewValue('abc')
    controller.$setValidity('response', false)
    controller.responseErrorMessage = 'fail'
    $scope.$digest()

    assert.include($field.prop('className'), 'form-field-error', 'Fail fast check')

    controller.$setViewValue('def')
    $scope.$digest()

    assert.notInclude($field.prop('className'), 'form-field-error')

  it 'should hide errors if the model is marked as pristine', ->
    $field.addClass('form-field-error')
    $input = $field.find('[name=username]')
    controller = $input.controller('ngModel')

    $input.triggerHandler('input')  # set dirty
    controller.$setValidity('response', false)
    controller.responseErrorMessage = 'fail'
    $scope.$digest()

    assert.include($field.prop('className'), 'form-field-error', 'Fail fast check')

    # Then clear it out and mark it as pristine
    controller.$setPristine()
    $scope.$digest()

    assert.notInclude($field.prop('className'), 'form-field-error')

  describe 'with form-validate', ->
    link = require('../form-input')().link

    it 'should register its model with the validator', ->
      model = {'$parsers': []}
      validator = {addControl: sinon.spy(), removeControl: sinon.spy()}
      link($scope, $field, null, [model, validator])
      assert.calledOnce(validator.addControl)
      assert.calledWith(validator.addControl, model)
      assert.notCalled(validator.removeControl)
      $scope.$destroy()
      assert.calledOnce(validator.removeControl)
      assert.calledWith(validator.removeControl, model)
