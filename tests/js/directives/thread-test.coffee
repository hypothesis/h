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
    it 'toggles whether or not the thread is collapsed', ->
      controller = createController()
      before = controller.isCollapsed()
      controller.toggleCollapsed()
      after = controller.isCollapsed()
      assert.equal(before, !after)

    it 'can accept an argument to force a particular state', ->
      controller = createController()
      controller.toggleCollapsed(true)
      assert.isTrue(controller.isCollapsed())
      controller.toggleCollapsed(true)
      assert.isTrue(controller.isCollapsed())
      controller.toggleCollapsed(false)
      assert.isFalse(controller.isCollapsed())
      controller.toggleCollapsed(false)
      assert.isFalse(controller.isCollapsed())

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
      controller.parent = {isCollapsed: -> true}
      assert.isFalse(controller.shouldShowAsReply())

    describe 'when the thread contains edits', ->
      beforeEach ->
        count.withArgs('edit').returns(1)

      it 'is true when the thread has no parent', ->
        assert.isTrue(controller.shouldShowAsReply())

      it 'is true when the parent thread is not collapsed', ->
        controller.parent = {isCollapsed: -> false}
        assert.isTrue(controller.shouldShowAsReply())

      it 'is true when the parent thread is collapsed', ->
        controller.parent = {isCollapsed: -> true}
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

  it 'pulses the current thread on an annotationUpdated event', ->
    $element.scope().$emit('annotationUpdate')
    assert.called(fakePulse)

  it 'does not pulse the thread if it is hidden (parent collapsed)', ->
    fakeParent = {
      controller: -> {isCollapsed: sinon.stub().returns(true)}
    }
    sandbox.stub(angular.element.prototype, 'parent').returns(fakeParent)
    $element.scope().$emit('annotationUpdate')
    assert.notCalled(fakePulse)

  it 'does not pulse the thread if it is hidden (grandparent collapsed)', ->
    fakeGrandParent = {
      controller: -> {isCollapsed: sinon.stub().returns(true)}
    }
    fakeParent = {
      controller: -> {isCollapsed: sinon.stub().returns(false)}
      parent: -> fakeGrandParent
    }
    sandbox.stub(angular.element.prototype, 'parent').returns(fakeParent)
    $element.scope().$emit('annotationUpdate')
    assert.notCalled(fakePulse)
