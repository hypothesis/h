assert = chai.assert

describe 'h.directives', ->
  $scope = null
  $compile = null
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

  beforeEach module('h.directives')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  describe '.formValidate', ->
    $element = null

    beforeEach ->
      $scope.model = {username: ''}

      template = '''
      <form form-validate data-form-validate-error-class="form-field-error" name="login" onsubmit="return false">
        <div class="form-field" data-error-class="form-field-error" data-target="username">
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

    it 'should apply an error class to an invalid field on "error" event', ->
      $scope.$emit('error', 'login')
      $element.controller('form').username.$setValidity('response', false)

      $field = $element.find('.form-field')
      assert.include $field.prop('className'), 'form-field-error'

    it 'should remove an error class on valid input on keyup', ->
      $scope.model.username = 'abc'
      $scope.$digest()

      $field = $element.find('.form-field').addClass('form-field-error')
      $element.find('[name=username]').keyup()

      assert.notInclude $field.prop('className'), 'form-field-error'

    it 'should not add an error class on invalid input on keyup', ->
      $scope.model.username = ''
      $scope.$digest()

      $field = $element.find('.form-field')
      $element.find('[name=username]').keyup()

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
      sinon.assert.calledWith(fakeWindow.open, '/u/bill')

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

      it 'opens with only the username', ->
        $element.find('.user').click()
        sinon.assert.calledWith(fakeWindow.open, '/u/jim')

  describe '.simpleSearch', ->
    $element = null
    beforeEach ->
      $scope.query = {}
      $scope.update = ->
      $scope.clear = ->

      template= '''
      <div class="simpleSearch"
            query="query"
            onsearch="update(this)"
            onclear="clear()">
      </div>
      '''

      $element = $compile(angular.element(template))($scope)
      $scope.$digest()

    it 'updates the search-bar', ->
      $scope.query = {query: "Test query"}
      $scope.$digest()
      assert.equal($scope.searchtext, $scope.query.query)

    it 'calls the given search function', ->
      $scope.query = {query: "Test query"}
      $scope.update = sinon.spy()
      $scope.$digest()
      $element.trigger('submit')
      sinon.assert.calledWith($scope.update, "Test query")

    it 'calls the given clear function', ->
      $scope.clear = sinon.spy()
      $element.find('.simple-search-clear').click()
      assert($scope.clear.called)

    it 'clears the search-bar', ->
      $scope.query = {query: "Test query"}
      $scope.$digest()
      $element.find('.simple-search-clear').click()
      assert.equal($scope.searchtext, '')

    it 'adds a class to the form when there is no input value', ->
      $form = $element.find('.simple-search-form')
      assert.include($form.prop('className'), 'simple-search-inactive')

    it 'removes the class from the form when there is an input value', ->
      $scope.query = {query: "Test query"}
      $scope.$digest()

      $form = $element.find('.simple-search-form')
      assert.notInclude($form.prop('className'), 'simple-search-inactive')
