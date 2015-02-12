assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h.directives.thread.ThreadController', ->
  $scope = null
  createController = null

  beforeEach module('h')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()

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

  describe '#shouldShowReply', ->
    count = null
    controller = null

    beforeEach ->
      controller = createController()
      count = sinon.stub()

    describe 'when root', ->
      beforeEach -> controller.isRoot = true

      describe 'and when not filtered', ->
        it 'shows the reply if the thread is not collapsed and has children', ->
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread is not collapsed and has no children', ->
          count.withArgs('message').returns(0)
          assert.isFalse(controller.shouldShowReply(count, false))

        it 'shows the reply if the thread is collapsed and has children', ->
          count.withArgs('message').returns(1)
          controller.collapsed = true
          assert.isTrue(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread is collapsed and has no children', ->
          count.withArgs('message').returns(0)
          controller.collapsed = true
          assert.isFalse(controller.shouldShowReply(count, false))

      describe 'and when filtered with children', ->
        it 'shows the reply if the thread is not collapsed', ->
          count.withArgs('match').returns(1)
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, true))

        it 'does not show the reply if the thread is not collapsed and the message count does not match the match count', ->
          count.withArgs('match').returns(0)
          count.withArgs('message').returns(1)
          assert.isFalse(controller.shouldShowReply(count, true))

    describe 'when reply', ->
      beforeEach -> controller.isRoot = false

      describe 'and when not filtered', ->
        it 'shows the reply if the thread is not collapsed and has children', ->
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread is not collapsed and has no children', ->
          count.withArgs('message').returns(0)
          assert.isFalse(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread is collapsed and has children', ->
          count.withArgs('message').returns(1)
          controller.collapsed = true
          assert.isFalse(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread is collapsed and has no children', ->
          count.withArgs('message').returns(0)
          controller.collapsed = true
          assert.isFalse(controller.shouldShowReply(count, false))

      describe 'and when filtered with children', ->
        it 'shows the reply if the thread is not collapsed', ->
          count.withArgs('match').returns(1)
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, true))

        it 'does not show the reply if the thread is not collapsed and the message count does not match the match count', ->
          count.withArgs('match').returns(0)
          count.withArgs('message').returns(1)
          assert.isFalse(controller.shouldShowReply(count, true))


describe 'h.directives.thread.thread', ->
  createElement = null
  $element = null
  fakePulse = null
  sandbox = null

  beforeEach module 'h', ($compileProvider) ->
    # The thread directive instantiates the annotation directive, which in turn
    # injects a whole bunch of other stuff (auth service, permissions service,
    # etc.) which we really don't want to have to mock individually here. As
    # such, it's easier to just mock out the whole annotation directive for now.
    $compileProvider.directive 'annotation', ->
      priority: 9999
      terminal: true
      template: ''
    return

  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakePulse = sandbox.spy()
    $provide.value 'pulse', fakePulse
    return

  beforeEach inject ($compile, $rootScope) ->
    createElement = (html) ->
      el = $compile(html or '<div thread></div>')($rootScope.$new())
      $rootScope.$digest()
      return el
    $element = createElement()

  afterEach ->
    sandbox.restore()

  it 'sets the threadRoot on the controller to false', ->
    controller = $element.controller('thread')
    assert.isFalse(controller.isRoot)

  it 'sets the threadRoot on the controller to true when the thread-root attr is set', ->
    $element = createElement('<div thread thread-root="true"></div>')
    controller = $element.controller('thread')
    assert.isTrue(controller.isRoot)

  it 'pulses the current thread on an annotationUpdated event', ->
    $element.scope().$emit('annotationUpdate')
    assert.called(fakePulse)

  it 'does not pulse the thread if it is hidden (parent collapsed)', ->
    fakeParent = {
      controller: -> {collapsed: true}
    }
    sandbox.stub(angular.element.prototype, 'parent').returns(fakeParent)
    $element.scope().$emit('annotationUpdate')
    assert.notCalled(fakePulse)

  it 'does not pulse the thread if it is hidden (grandparent collapsed)', ->
    fakeGrandParent = {
      controller: -> {collapsed: true}
    }
    fakeParent = {
      controller: -> {collapsed: false}
      parent: -> fakeGrandParent
    }
    sandbox.stub(angular.element.prototype, 'parent').returns(fakeParent)
    $element.scope().$emit('annotationUpdate')
    assert.notCalled(fakePulse)
