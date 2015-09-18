{module, inject} = angular.mock

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

      it 'defaults to collapsed if it is a top level annotation', ->
        assert.isTrue(controller.collapsed)

      it 'can accept an argument to force a particular state', ->
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(true)
        assert.isTrue(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)
        controller.toggleCollapsed(false)
        assert.isFalse(controller.collapsed)

      it 'allows collapsing the thread even if there are no replies', ->
        count.withArgs('message').returns(1)
        controller.toggleCollapsed()
        assert.isFalse(controller.collapsed)
        controller.toggleCollapsed()
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
