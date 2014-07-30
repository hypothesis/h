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
      $scope.model = {username: ''}

      template = '''
      <form form-validate data-form-validate-error-class="form-field-error" name="login" onsubmit="return false">
        <div class="form-field" data-error-class="form-field-error">
          <input type="text" class="" ng-model="model.username" name="username" required ng-minlength="3" />
        </div>
      </form>
      '''

      # Needs to be passed through angular.element() to work. Otherwise it
      # will not link the form-validate directive.
      $element = $compile(angular.element(template))($scope)
      $scope.$digest()

    it 'should apply an error class to an invalid field on change', ->
      $field = $element.find('.form-field')
      $element.find('[name=username]').val('ab').change()
      assert.include $field.prop('className'), 'form-field-error'

    it 'should remove an error class to an valid field on change', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]')
      $input.val('abc').change()
      assert.notInclude $field.prop('className'), 'form-field-error'

    it 'should apply an error class to an invalid field on submit', ->
      $field = $element.find('.form-field')
      $element.trigger('submit')
      assert.include $field.prop('className'), 'form-field-error'

    it 'should remove an error class from a valid field on submit', ->
      $scope.model.username = 'abc'
      $scope.$digest()

      $field = $element.find('.form-field').addClass('form-field-error')

      $element.trigger('submit')
      assert.notInclude $field.prop('className'), 'form-field-error'

    it 'should apply an error class if the form recieves errors after a submit action', ->
      $element.trigger('submit')
      $element.controller('form').username.$setValidity('response', false)

      $field = $element.find('.form-field')
      assert.include $field.prop('className'), 'form-field-error'

    it 'should remove an error class on valid input on keyup', ->
      $field = $element.find('.form-field').addClass('form-field-error')
      $input = $element.find('[name=username]').val('abc').trigger('input')
      $input.keyup()

      assert.notInclude $field.prop('className'), 'form-field-error'

    it 'should not add an error class on invalid input on keyup', ->
      $field = $element.find('.form-field')
      $input = $element.find('[name=username]').val('ab').trigger('input')
      $input.keyup()

      assert.notInclude $field.prop('className'), 'form-field-error'

  describe '.username', ->
    $element = null

    beforeEach ->
      $scope.model = 'acct:bill@127.0.0.1'

      $element = $compile('<username data-user="model"></username>')($scope)
      $scope.$digest()

    it 'renders with the username', ->
      text = $element.find('.user').text()
      assert.equal(text, 'bill')

    it 'opens a new window for the user when clicked', ->
      $element.find('.user').click()
      sinon.assert.calledWith(fakeWindow.open, '/u/bill@127.0.0.1')

    it 'prevents the default browser action on click', ->
      event = jQuery.Event('click')
      $element.find('.user').trigger(event)

      assert(event.isDefaultPrevented())

    describe 'when model is changed', ->
      beforeEach ->
        $scope.model = 'acct:jim@hypothesis'
        $scope.$digest()

      it 'keeps the username in sync', ->
        text = $element.find('.user').text()
        assert.equal(text, 'jim')

      it 'keeps the url in sync', ->
        $element.find('.user').click()
        sinon.assert.calledWith(fakeWindow.open, '/u/jim@hypothesis')

  describe '.match', ->
    $element = null

    beforeEach ->
      $scope.model = {a: 1, b: 1}

      $element = $compile('<input name="confirmation" ng-model="model.b" match="model.a" />')($scope)
      $scope.$digest()

    it 'is valid if both properties have the same value', ->
      controller = $element.controller('ngModel')
      assert.isFalse(controller.$error.match)

    # TODO: Work out how to watch for changes to the model.
    it 'is invalid if the local property differs'
    # it 'is invalid if the local property differs', ->
    #   $scope.model.b = 2
    #   $scope.$digest()

    #   controller = $element.controller('ngModel')
    #   assert.isTrue(controller.$error.match)

    it 'is invalid if the matched property differs', ->
      $scope.model.a = 2
      $scope.$digest()

      controller = $element.controller('ngModel')
      assert.isTrue(controller.$error.match)

    it 'is invalid if the input itself is changed', ->
      $element.val('2').trigger('input').keyup()

      controller = $element.controller('ngModel')
      assert.isTrue(controller.$error.match)

  describe '.userPicker', ->
    $element = null

    beforeEach ->
      $scope.model = 'acct:bill@localhost'
      $scope.options = []

      $element = $compile('<user-picker data-user-picker-model="model" data-user-picker-options="options"></user-picker>')($scope)
      $scope.$digest()

    it 'triggers the "nav:account" event when the Account item is clicked', (done) ->
      $scope.$on 'nav:account', ->
        done()
      $element.find('li', -> this.text == 'Account').click()
