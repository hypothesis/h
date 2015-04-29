{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'thread', ->
  $compile = null
  $element = null
  $scope = null
  controller = null
  fakePulse = null
  fakeRender = null
  sandbox = null

  createDirective = ->
    $element = angular.element('<div thread>')
    $compile($element)($scope)
    $scope.$digest()
    controller = $element.controller('thread')

  before ->
    angular.module('h', [])
    .directive('thread', require('../thread'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakePulse = sandbox.spy()
    fakeRender = sandbox.spy()
    $provide.value 'pulse', fakePulse
    $provide.value 'render', fakeRender
    return

  beforeEach inject (_$compile_, $rootScope) ->
    $compile = _$compile_
    $scope = $rootScope.$new()

  afterEach ->
    sandbox.restore()

  describe 'controller', ->

    it 'returns true from isNew() for a new annotation', ->
      createDirective()

      # When the user clicks to create a new annotation in the browser, we get
      # a ThreadController with a container with a message (the annotation)
      # with no id.
      controller.container = {message: {}}

      assert(controller.isNew())

    it 'returns false from isNew() for an old annotation', ->
      createDirective()

      # When we create a ThreadController for an old annotation, the controller
      # has a container with a message (the annotation) with an id.
      controller.container = {message: {id: 123}}

      assert(not controller.isNew())

    it 'returns false from isNew() for a null annotation', ->
      createDirective()

      # The ThreadController may be an empty container.
      controller.container = {}

      assert(not controller.isNew())

    describe '#toggleCollapsed', ->
      count = null

      beforeEach ->
        createDirective()
        count = sinon.stub().returns(0)
        count.withArgs('message').returns(2)
        controller.counter = {count: count}

      it 'toggles whether or not the thread is collapsed', ->
        before = controller.collapsed
        controller.toggleCollapsed()
        after = controller.collapsed
        assert.equal(before, !after)

      it 'can accept an argument to force a particular state', ->
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)

      it 'does not allow uncollapsing the thread if there are no replies', ->
        count.withArgs('message').returns(1)
        controller.toggleCollapsed()
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed()
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isTrue(controller.collapsed)

    describe '#shouldShowAsReply', ->
      count = null

      beforeEach ->
        createDirective()
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
      filterActive = false

      beforeEach ->
        createDirective()
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

      beforeEach ->
        createDirective()

      it 'returns zero when there is no counter', ->
        assert.equal(controller.numReplies(), 0)

      it 'returns one less than the number of messages in the thread when there is a counter', ->
        count = sinon.stub()
        count.withArgs('message').returns(5)
        controller.counter = {count: count}

        assert.equal(controller.numReplies(), 4)

    describe '#shouldShowLoadMore', ->

      beforeEach ->
        createDirective()

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

      beforeEach ->
        createDirective()

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

      beforeEach ->
        createDirective()

      it 'is true by default', ->
        assert.isTrue(controller.matchesFilter())

      it 'checks with the thread filter to see if the annotation matches', ->
        check = sinon.stub().returns(false)
        controller.filter = {check: check}
        controller.container = {}
        assert.isFalse(controller.matchesFilter())
        assert.calledWith(check, controller.container)

  describe 'directive', ->
    beforeEach ->
      createDirective()

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
