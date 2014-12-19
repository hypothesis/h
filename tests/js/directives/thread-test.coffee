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

  describe '#onAnnotationModeChange', ->
    it 'sets the inEditMode property to true when editing an annotation', ->
      controller = createController()
      controller.onAnnotationModeChange(value: 'edit', EDIT: 'edit', VIEW: 'view')
      assert.isTrue(controller.inEditMode)

    it 'sets the inEditMode property to false when viewing an annotation', ->
      controller = createController()
      controller.onAnnotationModeChange(value: 'view', EDIT: 'edit', VIEW: 'view')
      assert.isFalse(controller.inEditMode)


describe 'h.directives.thread.thread', ->
  $element = null
  fakePulse = null
  sandbox = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakePulse = sandbox.spy()
    $provide.value 'pulse', fakePulse
    return

  beforeEach inject ($compile, $rootScope) ->
    $element = $compile('<div thread></div>')($rootScope.$new())
    $isolateScope = $element.scope()

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
