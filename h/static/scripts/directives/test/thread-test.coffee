{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h:directives.thread', ->
  fakeRender = null
  sandbox = null

  before ->
    angular.module('h', [])
    require('../thread')

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakeRender = sandbox.spy()
    $provide.value 'render', fakeRender
    return

  afterEach ->
    sandbox.restore()

  describe '.ThreadController', ->
    $scope = null
    createController = null

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


  describe '.thread', ->
    createElement = null
    $element = null
    $isolateScope = null
    fakePulse = null

    beforeEach module ($provide) ->
      fakePulse = sandbox.spy()
      $provide.value 'pulse', fakePulse
      return

    beforeEach inject ($compile, $rootScope) ->
      createElement = (html) -> $compile(html or '<div thread></div>')($rootScope.$new())
      $element = createElement()
      $isolateScope = $element.scope()

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
