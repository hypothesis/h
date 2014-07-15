assert = chai.assert

describe 'h.directives', ->
  $scope = null
  $compile = null
  fakeWindow = null

  beforeEach module ($provide, $filterProvider) ->
    fakeWindow = {open: sinon.spy()}

    $provide.value('$window', fakeWindow)

    $filterProvider.register 'persona', ->
      (user, part) ->
        parts = user.slice(5).split('@')
        {username: parts[0], provider: parts[1]}[part]

    return

  beforeEach module('h.directives')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

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
