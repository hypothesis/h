{module, inject} = angular.mock

describe 'thread', ->
  $compile = null
  $element = null
  $scope = null
  controller = null
  fakeRender = null
  fakeAnnotationUI = null
  sandbox = null
  selectedAnnotations = []

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
    fakeRender = sandbox.spy()
    fakeAnnotationUI = {
      hasSelectedAnnotations: ->
        selectedAnnotations.length > 0
      isAnnotationSelected: (id) ->
        selectedAnnotations.indexOf(id) != -1
    }
    $provide.value 'render', fakeRender
    $provide.value 'annotationUI', fakeAnnotationUI
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

    describe '#shouldShow()', ->
      count = null

      beforeEach ->
        createDirective()
        count = sinon.stub().returns(0)
        controller.counter = {count: count}

      it 'is true by default', ->
        assert.isTrue(controller.shouldShow())

      describe 'when the thread root is an orphan', ->
        beforeEach ->
          $scope.feature = -> false
          controller.container =
            message:
              $orphan: true

        it 'returns false', ->
          assert.isFalse(controller.shouldShow())

      describe 'when the thread filter is active', ->
        beforeEach ->
          controller.filter = {active: -> true}

        it 'is false when there are no matches in the thread', ->
          assert.isFalse(controller.shouldShow())

        it 'is true when there are matches in the thread', ->
          count.withArgs('match').returns(1)
          assert.isTrue(controller.shouldShow())

        it 'is true when there are edits in the thread', ->
          count.withArgs('edit').returns(1)
          assert.isTrue(controller.shouldShow())

        it 'is true when the thread is new', ->
          controller.container =
            # message exists but there is no id field
            message: {}
          assert.isTrue(controller.shouldShow())

      describe 'when the thread root has a group', ->
        beforeEach ->
          controller.container =
            message:
              id: 123
              group: 'wibble'

      describe 'filters messages based on the selection', ->
        messageID = 456

        beforeEach ->
          controller.container =
            message:
              id: messageID

        it 'shows all annotations when there is no selection', ->
          assert.isTrue(controller.shouldShow())

        it 'hides annotations that are not selected', ->
          selectedAnnotations = ['some-other-message-id']
          assert.isFalse(controller.shouldShow())

        it 'shows annotations that are selected', ->
          selectedAnnotations = [messageID]
          assert.isTrue(controller.shouldShow())

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
