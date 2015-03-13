{module, inject} = require('angular-mock')

assert = chai.assert


describe 'h.directives.annotation', ->
  $compile = null
  $document = null
  $scope = null
  $timeout = null
  annotation = null
  createController = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeDrafts = null
  fakeFlash = null
  fakeMomentFilter = null
  fakePermissions = null
  fakePersonaFilter = null
  fakeStore = null
  fakeTimeHelpers = null
  fakeUrlEncodeFilter = null
  sandbox = null

  before ->
    angular.module('h', [])
    require('../annotation')

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakeAuth =
      user: 'acct:bill@localhost'
    fakeAnnotationMapper =
      createAnnotation: sandbox.stub().returns
        permissions:
          read: ['acct:bill@localhost']
          update: ['acct:bill@localhost']
          destroy: ['acct:bill@localhost']
          admin: ['acct:bill@localhost']
      deleteAnnotation: sandbox.stub()
    fakeAnnotationUI = {}
    fakeDrafts = {
      add: sandbox.stub()
      remove: sandbox.stub()
    }
    fakeFlash = sandbox.stub()
    fakeMomentFilter = sandbox.stub().returns('ages ago')
    fakePermissions = {
      isPublic: sandbox.stub().returns(true)
      isPrivate: sandbox.stub().returns(false)
      permits: sandbox.stub().returns(true)
      public: sandbox.stub().returns({read: ['everybody']})
      private: sandbox.stub().returns({read: ['justme']})
    }
    fakePersonaFilter = sandbox.stub().returnsArg(0)
    fakeTimeHelpers = {
      toFuzzyString: sandbox.stub().returns('a while ago')
      nextFuzzyUpdate: sandbox.stub().returns(30)
    }
    fakeUrlEncodeFilter = (v) -> encodeURIComponent(v)

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'auth', fakeAuth
    $provide.value 'drafts', fakeDrafts
    $provide.value 'flash', fakeFlash
    $provide.value 'momentFilter', fakeMomentFilter
    $provide.value 'permissions', fakePermissions
    $provide.value 'personaFilter', fakePersonaFilter
    $provide.value 'store', fakeStore
    $provide.value 'timeHelpers', fakeTimeHelpers
    $provide.value 'urlencodeFilter', fakeUrlEncodeFilter
    return

  beforeEach inject (_$compile_, $controller, _$document_, $rootScope, _$timeout_) ->
    $compile = _$compile_
    $document = _$document_
    $timeout = _$timeout_
    $scope = $rootScope.$new()
    $scope.annotationGet = (locals) -> annotation
    annotation =
      id: 'deadbeef'
      document:
        title: 'A special document'
      target: [{}]
      uri: 'http://example.com'
      user: 'acct:bill@localhost'

    createController = ->
      $controller 'AnnotationController',
        $scope: $scope

  afterEach ->
    sandbox.restore()

  describe '#reply', ->
    controller = null
    container = null

    beforeEach ->
      controller = createController()

      annotation.permissions =
        read: ['acct:joe@localhost']
        update: ['acct:joe@localhost']
        destroy: ['acct:joe@localhost']
        admin: ['acct:joe@localhost']

    it 'creates a new reply with the proper uri and references', ->
      controller.reply()
      match = sinon.match {references: [annotation.id], uri: annotation.uri}
      assert.calledWith(fakeAnnotationMapper.createAnnotation, match)

    it 'makes the annotation public if the parent is public', ->
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      fakePermissions.isPublic.returns(true)
      controller.reply()
      assert.deepEqual(reply.permissions, {read: ['everybody']})

    it 'does not add the world readable principal if the parent is private', ->
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      fakePermissions.isPublic.returns(false)
      controller.reply()
      assert.deepEqual(reply.permissions, {read: ['justme']})

  describe '#render', ->
    controller = null

    beforeEach ->
      controller = createController()
      sandbox.spy(controller, 'render')

    afterEach ->
      sandbox.restore()

    it 'is called exactly once during the first digest', ->
      $scope.$digest()
      assert.calledOnce(controller.render)

    it 'is called exactly once on model changes', ->
      $scope.$digest()
      assert.calledOnce(controller.render)
      $scope.$digest()
      assert.calledOnce(controller.render)  # still

      annotation.booz = 'baz'
      $scope.$digest()
      assert.calledTwice(controller.render)

    it 'provides a document title', ->
      controller.render()
      assert.equal(controller.document.title, 'A special document')

    it 'uses the first title when there are more than one', ->
      annotation.document.title = ['first title', 'second title']
      controller.render()
      assert.equal(controller.document.title, 'first title')

    it 'truncates long titles', ->
      annotation.document.title = '''A very very very long title that really
      shouldn't be found on a page on the internet.'''
      controller.render()
      assert.equal(controller.document.title, 'A very very very long title th…')

    it 'provides a document uri', ->
      controller.render()
      assert.equal(controller.document.uri, 'http://example.com')

    it 'provides an extracted domain from the uri', ->
      controller.render()
      assert.equal(controller.document.domain, 'example.com')

    it 'uses the domain for the title if the title is not present', ->
      delete annotation.document.title
      controller.render()
      assert.equal(controller.document.title, 'example.com')

    it 'skips the document object if no document is present on the annotation', ->
      delete annotation.document
      controller.render()
      assert.isNull(controller.document)

    describe 'when there are no targets', ->
      beforeEach ->
        annotation.target = []
        controller.render()
        targets = controller.annotation.target

      it 'sets `hasDiff` to false and `showDiff` to undefined', ->
        controller.render()
        assert.isFalse(controller.hasDiff)
        assert.isUndefined(controller.showDiff)

    describe 'when a single target has text identical to what was in the selectors', ->
      it 'sets `showDiff` to undefined and `hasDiff` to false', ->
        controller.render()
        assert.isFalse(controller.hasDiff)
        assert.isUndefined(controller.showDiff)

    describe 'when a single target has different text, compared to what was in the selector', ->
      targets = null

      beforeEach ->
        annotation.target = [
          {diffHTML: "This is <ins>not</ins> the same quote", diffCaseOnly: false},
        ]
        controller.render()
        targets = controller.annotation.target

      it 'sets both `hasDiff` and `showDiff` to true', ->
        controller.render()
        assert.isTrue(controller.hasDiff)
        assert.isTrue(controller.showDiff)

    describe 'when thre are only upper case/lower case difference between the text in the single target, and what was saved in a selector', ->
      targets = null

      beforeEach ->
        annotation.target = [
          {diffHTML: "<ins>s</ins><del>S</del>tuff", diffCaseOnly: true},
        ]
        controller.render()
        targets = controller.annotation.target

      it 'sets `hasDiff` to true and `showDiff` to false', ->
        controller.render()
        assert.isTrue(controller.hasDiff)
        assert.isFalse(controller.showDiff)

    describe 'when there are multiple targets, some with differences in text', ->
      targets = null

      beforeEach ->
        annotation.target = [
          {otherProperty: 'bar'},
          {diffHTML: "This is <ins>not</ins> the same quote", diffCaseOnly: false},
          {diffHTML: "<ins>s</ins><del>S</del>tuff", diffCaseOnly: true},
        ]
        controller.render()
        targets = controller.annotation.target

      it 'sets `hasDiff` to true', ->
        assert.isTrue(controller.hasDiff)

      it 'sets `showDiff` to true', ->
        assert.isTrue(controller.showDiff)

      it 'preserves the `showDiff` value on update', ->
        controller.showDiff = false
        annotation.target = annotation.target.slice(1)
        controller.render()
        assert.isFalse(controller.showDiff)

      it 'unsets `hasDiff` if differences go away', ->
        annotation.target = annotation.target.splice(0, 1)
        controller.render()
        assert.isFalse(controller.hasDiff)

    describe 'when there are multiple targets, some with differences, but only upper case / lower case', ->
      targets = null

      beforeEach ->
        annotation.target = [
          {otherProperty: 'bar'},
          {diffHTML: "<ins>s</ins><del>S</del>tuff", diffCaseOnly: true},
        ]
        controller.render()
        targets = controller.annotation.target

      it 'sets `hasDiff` to true', ->
        assert.isTrue(controller.hasDiff)

      it 'sets `showDiff` to false', ->
        assert.isFalse(controller.showDiff)

      it 'preserves the `showDiff` value on update', ->
        controller.showDiff = true
        annotation.target = annotation.target.slice(1)
        controller.render()
        assert.isTrue(controller.showDiff)

      it 'unsets `hasDiff` if differences go away', ->
        annotation.target = annotation.target.splice(0, 1)
        controller.render()
        assert.isFalse(controller.hasDiff)

    describe 'timestamp', ->
      clock = null

      beforeEach ->
        clock = sinon.useFakeTimers()
        annotation.created = (new Date()).toString()
        annotation.updated = (new Date()).toString()

      afterEach ->
        clock.restore()

      it 'is updated on first digest', ->
        $scope.$digest()
        assert.equal(controller.timestamp, 'a while ago')

      it 'is updated after a timeout', ->
        fakeTimeHelpers.nextFuzzyUpdate.returns(10)
        $scope.$digest()
        clock.tick(11000)
        fakeTimeHelpers.toFuzzyString.returns('ages ago')
        $timeout.flush()
        assert.equal(controller.timestamp, 'ages ago')

      it 'is no longer updated after the scope is destroyed', ->
        $scope.$digest()
        $scope.$destroy()
        $timeout.flush()
        $timeout.verifyNoPendingTasks()

    describe 'share', ->
      $element = null
      $isolateScope = null
      dialog = null

      beforeEach ->
        template = '<div annotation="annotation">'
        $scope.annotation = annotation
        $element = $compile(template)($scope)
        $scope.$digest()
        $isolateScope = $element.isolateScope()
        dialog = $element.find('.share-dialog-wrapper')

      it 'sets and unsets the open class on the share wrapper', ->
        $element.find('a').filter(-> this.title == 'Share').click()
        $isolateScope.$digest()
        assert.ok(dialog.hasClass('open'))
        $document.click()
        assert.notOk(dialog.hasClass('open'))

  describe 'annotationUpdate event', ->
    controller = null

    beforeEach ->
      controller = createController()
      sandbox.spy($scope, '$emit')
      annotation.updated = '123'
      $scope.$digest()

    it "does not fire when this user's annotations are updated", ->
      annotation.updated = '456'
      $scope.$digest()
      assert.notCalled($scope.$emit)

    it "fires when another user's annotation is updated", ->
      fakeAuth.user = 'acct:jane@localhost'
      annotation.updated = '456'
      $scope.$digest()
      assert.calledWith($scope.$emit, 'annotationUpdate')
