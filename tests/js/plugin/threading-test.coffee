assert = chai.assert
sinon.assert.expose(assert, prefix: null)
sandbox = sinon.sandbox.create()

describe 'Annotator.Threading', ->
  createThreadingInstance = (options) ->
    element = document.createElement('div')
    return new Annotator.Plugin.Threading(element, options || {})

  describe 'pruneEmpties', ->
    it 'keeps public messages with no children', ->
      threadA = mail.messageContainer(mail.message('subject a', 'a', []))
      threadB = mail.messageContainer(mail.message('subject b', 'b', []))
      threadC = mail.messageContainer(mail.message('subject c', 'c', []))

      root = mail.messageContainer()
      root.addChild(threadA)
      root.addChild(threadB)
      root.addChild(threadC)

      instance = createThreadingInstance()
      instance.pruneEmpties(root)

      assert.equal(root.children.length, 3)

    it 'keeps public messages with public children', ->
      threadA = mail.messageContainer(mail.message('subject a', 'a', []))
      threadA1 = mail.messageContainer(mail.message('subject a1', 'a1', ['a']))
      threadA2 = mail.messageContainer(mail.message('subject a2', 'a2', ['a']))

      root = mail.messageContainer()
      root.addChild(threadA)

      threadA.addChild(threadA1)
      threadA.addChild(threadA2)

      instance = createThreadingInstance()
      instance.pruneEmpties(root)

      assert.equal(root.children.length, 1)

    it 'prunes private messages with no children', ->
      threadA = mail.messageContainer()
      threadB = mail.messageContainer()
      threadC = mail.messageContainer()

      root = mail.messageContainer()
      root.addChild(threadA)
      root.addChild(threadB)
      root.addChild(threadC)

      instance = createThreadingInstance()
      instance.pruneEmpties(root)

      assert.equal(root.children.length, 0)

    it 'keeps private messages with public children', ->
      threadA = mail.messageContainer()
      threadA1 = mail.messageContainer(mail.message('subject a1', 'a1', ['a']))
      threadA2 = mail.messageContainer(mail.message('subject a2', 'a2', ['a']))

      root = mail.messageContainer()
      root.addChild(threadA)

      threadA.addChild(threadA1)
      threadA.addChild(threadA2)

      instance = createThreadingInstance()
      instance.pruneEmpties(root)

      assert.equal(root.children.length, 1)

    it 'prunes private messages with private children', ->
      threadA = mail.messageContainer()
      threadA1 = mail.messageContainer()
      threadA2 = mail.messageContainer()

      root = mail.messageContainer()
      root.addChild(threadA)

      threadA.addChild(threadA1)
      threadA.addChild(threadA2)

      instance = createThreadingInstance()
      instance.pruneEmpties(root)

      assert.equal(root.children.length, 0)

  describe 'handles events', ->
    annotator = null
    instance = null

    beforeEach ->
      instance = createThreadingInstance()
      instance.pluginInit()
      annotator =
        publish: (event, args) ->
          unless angular.isArray(args) then args = [args]
          meth = instance.events[event]
          instance[meth].apply(instance, args)

    afterEach ->
      sandbox.restore()

    it 'calls the thread method on beforeAnnotationCreated', ->
      annotation = {id: 'foo'}
      sandbox.spy(instance, 'thread')
      annotator.publish 'beforeAnnotationCreated', annotation
      assert.calledWithMatch instance.thread, [annotation]

    it 'calls the thread method on annotationsLoaded', ->
      annotation = {id: 'foo'}
      sandbox.spy(instance, 'thread')
      annotator.publish 'annotationsLoaded', [annotation]
      assert.calledWithMatch instance.thread, [annotation]

    it 'removes matching top level threads when annotationDeleted is called', ->
      annotation = {id: 'foo'}
      instance.thread([annotation])

      assert.equal(instance.root.children.length, 1)
      assert.equal(instance.idTable['foo'].message, annotation)

      sandbox.spy(instance, 'pruneEmpties')
      annotator.publish 'annotationDeleted', annotation
      assert.called(instance.pruneEmpties)

      assert.equal(instance.root.children.length, 0)
      assert.isUndefined(instance.idTable['foo'])

    it 'removes matching reply threads when annotationDeleted is called', ->
      parent = {id: 'foo'}
      reply = {id: 'bar', references: ['foo']}
      instance.thread([parent, reply])

      assert.equal(instance.idTable['foo'].children.length, 1)
      assert.equal(instance.idTable['bar'].message, reply)

      sandbox.spy(instance, 'pruneEmpties')
      annotator.publish 'annotationDeleted', reply
      assert.called(instance.pruneEmpties)

      assert.equal(instance.idTable['foo'].children.length, 0)
      assert.isUndefined(instance.idTable['bar'])
