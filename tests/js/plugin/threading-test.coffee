assert = chai.assert
sinon.assert.expose(assert, prefix: '')

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

  describe 'when @shouldRemoveEmptyParents is set to true', ->
    it 'promotes children with empty parents to the root', ->
      threadA = mail.messageContainer()
      threadA1 = mail.messageContainer()
      threadA11 = mail.messageContainer(mail.message('subject a11', 'a11'))

      root = mail.messageContainer()
      root.addChild(threadA)
      threadA.addChild(threadA1)
      threadA1.addChild(threadA11)

      instance = createThreadingInstance()
      instance.shouldRemoveEmptyParents = true
      instance.pruneEmpties(root)

      assert.equal(root.children[0], threadA11)
