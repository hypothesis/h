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

    describe '#shouldShowAsReply', ->
      controller = null
      count = null

      beforeEach ->
        controller = createController()
        count = sinon.stub().returns(0)
        controller.counter = {count: count}

      it 'is true by default', ->
        assert.isTrue(controller.shouldShowAsReply())

      it 'is false when the parent thread is collapsed', ->
        controller.parent = {collapsed: true}
        assert.isFalse(controller.shouldShowAsReply())

      describe 'when the thread contains edits', ->
        beforeEach ->
          count.withArgs('edit').returns(1)

        it 'is true when the thread has no parent', ->
          assert.isTrue(controller.shouldShowAsReply())

        it 'is true when the parent thread is not collapsed', ->
          controller.parent = {collapsed: false}
          assert.isTrue(controller.shouldShowAsReply())

        it 'is true when the parent thread is collapsed', ->
          controller.parent = {collapsed: true}
          assert.isTrue(controller.shouldShowAsReply())

      describe 'when the thread filter is active', ->
        beforeEach ->
          controller.filter = {active: -> true}

        it 'is false when there are no matches in the thread', ->
          assert.isFalse(controller.shouldShowAsReply())

        it 'is true when there are matches in the thread', ->
          count.withArgs('match').returns(1)
          assert.isTrue(controller.shouldShowAsReply())

    describe '#shouldShowNumReplies', ->
      count = null
      controller = null
      filterActive = false

      beforeEach ->
        controller = createController()
        count = sinon.stub()
        controller.counter = {count: count}
        controller.filter = {active: -> filterActive}

      describe 'when not filtered', ->
        it 'shows the reply if the thread has children', ->
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowNumReplies())

        it 'does not show the reply if the thread has no children', ->
          count.withArgs('message').returns(0)
          assert.isFalse(controller.shouldShowNumReplies())

      describe 'when filtered with children', ->
        beforeEach ->
          filterActive = true

        it 'shows the reply', ->
          count.withArgs('match').returns(1)
          count.withArgs('message').returns(1)
          assert.isTrue(controller.shouldShowNumReplies())

        it 'does not show the reply if the message count does not match the match count', ->
          count.withArgs('match').returns(0)
          count.withArgs('message').returns(1)
          assert.isFalse(controller.shouldShowNumReplies())

    describe '#numReplies', ->
      controller = null

      beforeEach ->
        controller = createController()

      it 'returns zero when there is no counter', ->
        assert.equal(controller.numReplies(), 0)

      it 'returns one less than the number of messages in the thread when there is a counter', ->
        count = sinon.stub()
        count.withArgs('message').returns(5)
        controller.counter = {count: count}

        assert.equal(controller.numReplies(), 4)

    describe '#shouldShowLoadMore', ->
      controller = null

      beforeEach ->
        controller = createController()

      describe 'when the thread filter is not active', ->
        it 'is false with an empty container', ->
          assert.isFalse(controller.shouldShowLoadMore())

        it 'is false when the container contains an annotation', ->
          controller.container = {message: {id: 123}}
          assert.isFalse(controller.shouldShowLoadMore())

      describe 'when the thread filter is active', ->
        beforeEach ->
          controller.filter = {active: -> true}

        it 'is false with an empty container', ->
          assert.isFalse(controller.shouldShowLoadMore())

        it 'is true when the container contains an annotation', ->
          controller.container = {message: {id: 123}}
          assert.isTrue(controller.shouldShowLoadMore())

    describe '#loadMore', ->
      controller = null

      beforeEach ->
        controller = createController()

      it 'uncollapses the thread', ->
        sinon.spy(controller, 'toggleCollapsed')
        controller.loadMore()
        assert.calledWith(controller.toggleCollapsed, false)

      it 'uncollapses all the ancestors of the thread', ->
        grandmother = {toggleCollapsed: sinon.stub()}
        mother = {toggleCollapsed: sinon.stub()}
        controller.parent = mother
        controller.parent.parent = grandmother
        controller.loadMore()
        assert.calledWith(mother.toggleCollapsed, false)
        assert.calledWith(grandmother.toggleCollapsed, false)

      it 'deactivates the thread filter when present', ->
        controller.filter = {active: sinon.stub()}
        controller.loadMore()
        assert.calledWith(controller.filter.active, false)

    describe '#matchesFilter', ->
      controller = null

      beforeEach ->
        controller = createController()

      it 'is true by default', ->
        assert.isTrue(controller.matchesFilter())

      it 'checks with the thread filter to see if the root annotation matches', ->
        check = sinon.stub().returns(false)
        controller.filter = {check: check}
        controller.container = {}
        assert.isFalse(controller.matchesFilter())
        assert.calledWith(check, controller.container)


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
