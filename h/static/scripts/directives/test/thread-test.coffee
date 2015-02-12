{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'h:directives.thread', ->

  before ->
    angular.module('h', [])
    require('../thread')

  describe '.ThreadController', ->
    $scope = null
    createController = null

    beforeEach module('h')

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()

      createController = ->
        controller = $controller 'ThreadController'
        controller

    describe '#toggleCollapsed', ->
      it 'toggles whether or not the thread is collapsed', ->
        controller = createController()
        before = controller.collapsed
        controller.toggleCollapsed()
        after = controller.collapsed
        assert.equal(before, !after)

      it 'can accept an argument to force a particular state', ->
        controller = createController()
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)

    describe '#shouldShowReply', ->
      count = null
      controller = null

      beforeEach ->
        controller = createController()
        count = sinon.stub()

      describe 'when not filtered', ->
        it 'shows the reply if the thread has children', ->
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, false))

        it 'does not show the reply if the thread has no children', ->
          count.withArgs('message').returns(0)
          assert.isFalse(controller.shouldShowReply(count, false))

      describe 'when filtered with children', ->
        it 'shows the reply', ->
          count.withArgs('match').returns(1)
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowReply(count, true))

        it 'does not show the reply if the message count does not match the match count', ->
          count.withArgs('match').returns(0)
          count.withArgs('message').returns(1)
          assert.isFalse(controller.shouldShowReply(count, true))


  describe '.thread', ->
    createElement = null
    $element = null
    fakePulse = null
    fakeRender = null
    sandbox = null

    beforeEach module('h')

    beforeEach module ($provide) ->
      sandbox = sinon.sandbox.create()
      fakePulse = sandbox.spy()
      fakeRender = sandbox.spy()
      $provide.value 'pulse', fakePulse
      $provide.value 'render', fakeRender
      return

    beforeEach inject ($compile, $rootScope) ->
      $element = $compile('<div thread></div>')($rootScope.$new())
      $rootScope.$digest()

    afterEach ->
      sandbox.restore()

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
