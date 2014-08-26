assert = chai.assert
sandbox = sinon.sandbox.create()

describe 'h.directives.thread', ->
  $attrs = null
  $scope = null
  $element = null
  container = null
  createController = null

  beforeEach module('h.directives')

  beforeEach inject ($controller, $rootScope) ->
    $attrs =
      $addClass: sinon.spy()
      $removeClass: sinon.spy()
      thread: 'thread'
    $scope = $rootScope.$new()
    render = (value, cb) -> cb(value)

    createController = ->
      $scope.thread = mail.messageContainer()
      $scope.thread.message = id: 'foo', uri: 'http://example.com/'
      $element = angular.element('<div thread="thread"><input /></div>')
      $controller 'ThreadController', {$attrs, $element, $scope, render}

  afterEach ->
    sandbox.restore()

  it 'sets its initial collapsed state', ->
    controller = createController()
    $scope.$digest()
    assert.equal(controller.collapsed, false, 'defaults to false')

    $attrs.threadCollapsed = 'true'
    controller = createController()
    $scope.$digest()
    assert.equal(controller.collapsed, true, 'accepts a boolean value')

  describe '#reply', ->
    controller = null
    container = null
    children = null
    message = null

    beforeEach ->
      controller = createController()
      container = $scope.thread
      message = container.message

    it 'expands if collapsed', ->
      controller.reply()
      assert.equal(controller.collapsed, false)

    it 'creates a new reply and adds it to the container', ->
      controller.reply()
      assert.equal(container.children.length, 1)

    it 'copies the id uri from the parent', ->
      controller.reply()
      reply = container.children[0].message
      assert.equal(reply.uri, message.uri)

    it 'adds a reference to the parent message to the reply', ->
      controller.reply()
      reply = container.children[0]
      assert.deepEqual(reply.message.references, [message.id])
      container.removeChild(reply)

      message.references = ['top']
      controller.reply()
      reply = container.children[0]
      assert.deepEqual(reply.message.references, ['top', message.id])

  describe '#toggleCollapsed', ->
    it 'sets the collapsed property', ->
      controller = createController()
      before = controller.collapsed
      controller.toggleCollapsed()
      after = controller.collapsed
      assert.equal(before, !after)

    it 'adds and removes the collapsed class', ->
      controller = createController()
      controller.toggleCollapsed()
      assert.calledWith($attrs.$addClass, 'thread-collapsed')
      controller.toggleCollapsed()
      assert.calledWith($attrs.$removeClass, 'thread-collapsed')

    it 'broadcasts the threadCollapse event', ->
      $scope.$on 'threadCollapse', (event) ->
        event.preventDefault()
      sandbox.spy($scope, '$broadcast')
      controller = createController()
      before = controller.collapsed
      controller.toggleCollapsed()
      after = controller.collapsed
      assert.called($scope.$broadcast)
      assert.equal(before, after)

  describe '#toggleShared', ->
    it 'sets the shared property', ->
      controller = createController()
      before = controller.shared
      controller.toggleShared()
      after = controller.shared
      assert.equal(before, !after)

    it 'focuses the first input element', ->
      sandbox.spy(jQuery.fn, 'focus')
      controller = createController()
      controller.toggleShared()
      inject(($timeout) -> $timeout.flush())
      input = $element.find('input')
      assert.deepEqual(jQuery.fn.focus.thisValues[0], input)
