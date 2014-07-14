assert = chai.assert

describe 'h.directives', ->
  $scope = null
  $compile = null
  fakeWindow = null

  beforeEach module ($provide, $filterProvider) ->
    fakeWindow = {open: sinon.spy()}

    $provide.value('$window', fakeWindow)

    # Return filter key rather than value.
    $filterProvider.register 'persona', ->
      (obj, value) -> value
    return

  beforeEach module('h.directives')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  describe '.username', ->
    $element = null

    beforeEach ->
      $scope.user = 'acct:bill@127.0.0.1'

      $element = $compile('<username ng-model="user"></username>')($scope)
      $scope.$digest()

    it 'renders with the username', ->
      text = $element.find('.user').text()
      assert(text, 'username')

    it 'runs successfully', ->
      $element.find('.user').click()
      sinon.assert.calledWith(fakeWindow.open, '/u/username@provider')
