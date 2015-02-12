assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h.directives.threadList.ThreadListController', ->
  $scope = null
  createController = null

  beforeEach module('h')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()

    createController = ->
      controller = $controller('ThreadListController', $scope: $scope)
      controller

  describe '.container', ->
    it 'retrieves the container from its scope', ->
      $scope.getContainer = sinon.stub().returns(123)
      controller = createController()
      assert.equal(controller.container, 123)


describe 'h.directives.threadList.threadList', ->
  createElement = null
  $element = null
  $scope = null
  sandbox = null

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    return

  beforeEach inject ($compile, $rootScope) ->
    $scope = $rootScope.$new()

    createElement = (html) ->
      el = $compile(html or '<div thread-list></div>')($scope)
      $scope.$digest()
      return el

  afterEach ->
    sandbox.restore()

  it 'uses the thread-list attribute to provide the container', ->
    container = {}
    $scope.myContainer = container
    $element = createElement('<div thread-list="myContainer"></div>')
    assert.strictEqual($element.isolateScope().getContainer(), container)
