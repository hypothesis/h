assert = chai.assert

describe 'h.directives.thread', ->
  $attrs = null
  $scope = null
  $element = null
  container = null
  createController = null
  flash = null

  beforeEach module('h')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    flash = sinon.spy()

    createController = ->
      controller = $controller 'ThreadController'
      controller

  describe '#toggleCollapsed', ->
    it 'sets the collapsed property', ->
      controller = createController()
      before = controller.collapsed
      controller.toggleCollapsed()
      after = controller.collapsed
      assert.equal(before, !after)
