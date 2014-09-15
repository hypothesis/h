assert = chai.assert
sandbox = sinon.sandbox.create()

describe 'h.directives.thread', ->
  $attrs = null
  $scope = null
  $element = null
  container = null
  createController = null
  flash = null

  beforeEach module('h.directives')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    flash = sinon.spy()

    createController = ->
      controller = $controller 'ThreadController'
      controller.container = mail.messageContainer()
      controller.container.message = id: 'foo', uri: 'http://example.com/'
      controller

  afterEach ->
    sandbox.restore()

  describe '#reply', ->
    controller = null
    container = null
    children = null
    message = null

    beforeEach ->
      controller = createController()
      {container} = controller
      {message} = container

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

  describe '#toggleShared', ->
    it 'sets the shared property', ->
      controller = createController()
      before = controller.shared
      controller.toggleShared()
      after = controller.shared
      assert.equal(before, !after)
