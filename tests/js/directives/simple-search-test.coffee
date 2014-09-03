assert = chai.assert

describe 'h.directives', ->
  $scope = null
  $compile = null
  fakeWindow = null
  isolate = null

  beforeEach module('h.directives')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  describe '.simpleSearch', ->
    $element = null
    beforeEach ->
      $scope.update = sinon.spy()
      $scope.clear = sinon.spy()

      template= '''
      <div class="simpleSearch"
            query="query"
            on-search="update(query)"
            on-clear="clear()">
      </div>
      '''

      $element = $compile(angular.element(template))($scope)
      $scope.$digest()
      isolate = $element.isolateScope()

    it 'updates the search-bar', ->
      $scope.query = "Test query"
      $scope.$digest()
      assert.equal(isolate.searchtext, $scope.query)

    it 'calls the given search function', ->
      isolate.searchtext = "Test query"
      isolate.$digest()
      $element.find('form').triggerHandler('submit')
      sinon.assert.calledWith($scope.update, "Test query")

    it 'calls the given clear function', ->
      $element.find('.simple-search-clear').click()
      assert($scope.clear.called)

    it 'clears the search-bar', ->
      isolate.searchtext = "Test query"
      isolate.$digest()
      $element.find('.simple-search-clear').click()
      assert.equal(isolate.searchtext, '')

    it 'adds a class to the form when there is no input value', ->
      $form = $element.find('.simple-search-form')
      assert.include($form.prop('className'), 'simple-search-inactive')

    it 'removes the class from the form when there is an input value', ->
      $scope.query = "Test query"
      $scope.$digest()

      $form = $element.find('.simple-search-form')
      assert.notInclude($form.prop('className'), 'simple-search-inactive')
