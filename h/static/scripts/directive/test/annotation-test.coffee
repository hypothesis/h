{module, inject} = angular.mock

describe 'annotation', ->
  $compile = null
  $document = null
  $element = null
  $q = null
  $rootScope = null
  $scope = null
  $timeout = null
  annotation = null
  controller = null
  isolateScope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeDrafts = null
  fakeFeatures = null
  fakeFlash = null
  fakeGroups = null
  fakeMomentFilter = null
  fakePermissions = null
  fakePersonaFilter = null
  fakeDocumentTitleFilter = null
  fakeDocumentDomainFilter = null
  fakeSession = null
  fakeStore = null
  fakeTags = null
  fakeTime = null
  fakeUrlEncodeFilter = null
  fakeLocalStorage = null
  sandbox = null

  createDirective = ->
    $element = angular.element('<div annotation="annotation">')
    $compile($element)($scope)
    $scope.$digest()
    controller = $element.controller('annotation')
    isolateScope = $element.isolateScope()

  before ->
    angular.module('h', [])
    .directive('annotation', require('../annotation'))

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
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
    fakeFeatures = {
      flagEnabled: sandbox.stub().returns(true)
    }
    fakeFlash = sandbox.stub()

    fakeMomentFilter = sandbox.stub().returns('ages ago')
    fakePermissions = {
      isShared: sandbox.stub().returns(true)
      isPrivate: sandbox.stub().returns(false)
      permits: sandbox.stub().returns(true)
      shared: sandbox.stub().returns({read: ['everybody']})
      private: sandbox.stub().returns({read: ['justme']})
    }
    fakePersonaFilter = sandbox.stub().returnsArg(0)
    fakeDocumentTitleFilter = (arg) -> ''
    fakeDocumentDomainFilter = (arg) -> ''

    fakeSession =
      state:
        userid: 'acct:bill@localhost'

    fakeTags = {
      filter: sandbox.stub().returns('a while ago'),
      store: sandbox.stub()
    }
    fakeTime = {
      toFuzzyString: sandbox.stub().returns('a while ago')
      nextFuzzyUpdate: sandbox.stub().returns(30)
    }
    fakeUrlEncodeFilter = (v) -> encodeURIComponent(v)
    fakeLocalStorage = {
      setItem: sandbox.stub()
      getItem: sandbox.stub()
    }

    fakeGroups = {
      focused: -> {}
      get: ->
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'drafts', fakeDrafts
    $provide.value 'features', fakeFeatures
    $provide.value 'flash', fakeFlash
    $provide.value 'momentFilter', fakeMomentFilter
    $provide.value 'permissions', fakePermissions
    $provide.value 'personaFilter', fakePersonaFilter
    $provide.value('documentTitleFilter', fakeDocumentTitleFilter)
    $provide.value('documentDomainFilter', fakeDocumentDomainFilter)
    $provide.value 'session', fakeSession
    $provide.value 'store', fakeStore
    $provide.value 'tags', fakeTags
    $provide.value 'time', fakeTime
    $provide.value 'urlencodeFilter', fakeUrlEncodeFilter
    $provide.value 'localStorage', fakeLocalStorage
    $provide.value 'groups', fakeGroups
    return

  beforeEach inject (_$compile_, _$document_, _$q_, _$rootScope_, _$timeout_) ->
    $compile = _$compile_
    $document = _$document_
    $q = _$q_
    $timeout = _$timeout_
    $rootScope = _$rootScope_
    $scope = $rootScope.$new()
    $scope.annotation = annotation =
      id: 'deadbeef'
      document:
        title: 'A special document'
      target: [{}]
      uri: 'http://example.com'
      user: 'acct:bill@localhost'

  afterEach ->
    sandbox.restore()

  describe 'when the annotation is a highlight', ->
    beforeEach ->
      annotation.$highlight = true
      annotation.$create = sinon.stub().returns
        then: angular.noop
        catch: angular.noop
        finally: angular.noop

    it 'persists upon login', ->
      delete annotation.id
      delete annotation.user
      fakeSession.state.userid = null
      createDirective()
      $scope.$digest()
      assert.notCalled annotation.$create
      fakeSession.state.userid = 'acct:ted@wyldstallyns.com'
      $scope.$digest()
      assert.calledOnce annotation.$create

    it 'is private', ->
      delete annotation.id
      createDirective()
      $scope.$digest()
      assert.deepEqual annotation.permissions, {read: ['justme']}

  describe '#reply', ->
    container = null

    beforeEach ->
      createDirective()

      annotation.permissions =
        read: ['acct:joe@localhost']
        update: ['acct:joe@localhost']
        destroy: ['acct:joe@localhost']
        admin: ['acct:joe@localhost']

    it 'creates a new reply with the proper uri and references', ->
      controller.reply()
      match = sinon.match {references: [annotation.id], uri: annotation.uri}
      assert.calledWith(fakeAnnotationMapper.createAnnotation, match)

    it 'makes the annotation shared if the parent is shared', ->
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      fakePermissions.isShared.returns(true)
      controller.reply()
      assert.deepEqual(reply.permissions, {read: ['everybody']})

    it 'makes the annotation shared if the parent is shared', ->
      $scope.annotation.group = "my group"
      $scope.annotation.permissions = {read: ["my group"]}
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      fakePermissions.isShared = (permissions, group) ->
        return group in permissions.read
      fakePermissions.shared = (group) ->
        return {read: [group]}

      controller.reply()

      assert "my group" in reply.permissions.read

    it 'does not add the world readable principal if the parent is private', ->
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      fakePermissions.isShared.returns(false)
      controller.reply()
      assert.deepEqual(reply.permissions, {read: ['justme']})

    it "sets the reply's group to be the same as its parent's", ->
      $scope.annotation.group = "my group"
      reply = {}
      fakeAnnotationMapper.createAnnotation.returns(reply)
      controller.reply()
      assert.equal(reply.group, $scope.annotation.group)

  describe '#setPrivacy', ->
    beforeEach ->
      createDirective()

    it 'makes the annotation private when level is "private"', ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      controller.edit();
      controller.setPrivacy('private')
      controller.save().then(->
        # verify that the permissions are updated once the annotation
        # is saved
        assert.deepEqual(annotation.permissions, {read: ['justme']})
      )

    it 'makes the annotation shared when level is "shared"', ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      controller.edit();
      controller.setPrivacy('shared')
      controller.save().then(->
        assert.deepEqual(annotation.permissions, {read: ['everybody']})
      )

    it 'saves the "shared" visibility level to localStorage', ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      controller.edit();
      controller.setPrivacy('shared')
      controller.save().then(->
        assert(fakeLocalStorage.setItem.calledWithExactly(
          'hypothesis.privacy', 'shared'))
      )

    it 'saves the "private" visibility level to localStorage', ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      controller.edit();
      controller.setPrivacy('private')
      controller.save().then(->
        assert(fakeLocalStorage.setItem.calledWithExactly(
          'hypothesis.privacy', 'private'))
      )

    it "doesn't save the visibility if the annotation is a reply", ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      annotation.references = ["parent id"]
      controller.edit();
      controller.setPrivacy('private')
      controller.save().then(->
        assert(not fakeLocalStorage.setItem.called)
      )

  describe '#hasContent', ->
    beforeEach ->
      createDirective()

    it 'returns false if the annotation has no tags or text', ->
      controller.annotation.text = ''
      controller.annotation.tags = [];
      assert.ok(!controller.hasContent())

    it 'returns true if the annotation has tags or text', ->
      controller.annotation.text = 'bar'
      assert.ok(controller.hasContent())
      controller.annotation.text = ''
      controller.annotation.tags = [{text: 'foo'}]
      assert.ok(controller.hasContent())

  describe '#render', ->

    beforeEach ->
      createDirective()
      sandbox.spy(controller, 'render')

    afterEach ->
      sandbox.restore()

    it 'is called exactly once on model changes', ->
      assert.notCalled(controller.render)
      annotation.delete = true
      $scope.$digest()
      assert.calledOnce(controller.render)

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

    it 'still sets the uri correctly if the annotation has no document', ->
      delete annotation.document
      controller.render()
      assert(controller.document.uri == $scope.annotation.uri)

    it 'still sets the domain correctly if the annotation has no document', ->
      delete annotation.document
      controller.render()
      assert(controller.document.domain == 'example.com')

    it 'uses the domain for the title when the annotation has no document', ->
      delete annotation.document
      controller.render()
      assert(controller.document.title == 'example.com')

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

    describe 'when there are only upper case/lower case difference between the text in the single target, and what was saved in a selector', ->
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
        fakeTime.nextFuzzyUpdate.returns(10)
        $scope.$digest()
        clock.tick(11000)
        fakeTime.toFuzzyString.returns('ages ago')
        $timeout.flush()
        assert.equal(controller.timestamp, 'ages ago')

      it 'is no longer updated after the scope is destroyed', ->
        $scope.$digest()
        $scope.$destroy()
        $timeout.flush()
        $timeout.verifyNoPendingTasks()

    describe 'share', ->
      dialog = null

      beforeEach ->
        dialog = $element.find('.share-dialog-wrapper')

      it 'sets and unsets the open class on the share wrapper', ->
        dialog.find('button').click()
        isolateScope.$digest()
        assert.ok(dialog.hasClass('open'))
        $document.click()
        assert.notOk(dialog.hasClass('open'))

  describe "deleteAnnotation() method", ->
    before ->
      sinon.stub(window, "confirm")

    beforeEach ->
      createDirective()
      fakeAnnotationMapper.deleteAnnotation = sandbox.stub()
      fakeFlash.error = sandbox.stub()

    it "calls annotationMapper.delete() if the delete is confirmed", (done) ->
      window.confirm.returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.resolve())

      controller.delete().then ->
        assert fakeAnnotationMapper.deleteAnnotation.calledWith(annotation)
        done()
      $timeout.flush()

    it "doesn't call annotationMapper.delete() if the delete is cancelled", ->
      window.confirm.returns(false)
      assert fakeAnnotationMapper.deleteAnnotation.notCalled

    it "flashes a generic error if the server cannot be reached", (done) ->
      window.confirm.returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.reject({status: 0}))

      controller.delete().then ->
        assert fakeFlash.error.calledWith(
          "Service unreachable.", "Deleting annotation failed")
        done()
      $timeout.flush()

    it "flashes an error if the delete fails on the server", (done) ->
      window.confirm.returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.reject({
          status: 500,
          statusText: "Server Error",
          data: {}
        })
      )

      controller.delete().then ->
        assert fakeFlash.error.calledWith(
          "500 Server Error", "Deleting annotation failed")
        done()
      $timeout.flush()

    it "doesn't flash an error if the delete succeeds", (done) ->
      window.confirm.returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.resolve())

      controller.delete().then ->
        assert fakeFlash.error.notCalled
        done()
      $timeout.flush()

  describe "saving a new annotation", ->
    beforeEach ->
      createDirective()
      fakeFlash.error = sandbox.stub()
      controller.action = 'create'
      annotation.$create = sandbox.stub()

    it "emits annotationCreated when saving an annotation succeeds", (done) ->
      sandbox.spy($rootScope, '$emit')
      annotation.$create.returns(Promise.resolve())
      controller.save().then ->
        assert $rootScope.$emit.calledWith("annotationCreated")
        done()

    it "flashes a generic error if the server cannot be reached", (done) ->
      annotation.$create.returns(Promise.reject({status: 0}))

      controller.save().then ->
        assert fakeFlash.error.calledWith(
          "Service unreachable.", "Saving annotation failed")
        done()
      $timeout.flush()

    it "flashes an error if saving the annotation fails on the server", (done) ->
      annotation.$create.returns(Promise.reject({
          status: 500,
          statusText: "Server Error",
          data: {}
        })
      )
      controller.save().then ->
        assert fakeFlash.error.calledWith(
          "500 Server Error", "Saving annotation failed")
        done()

    it "doesn't flash an error when saving an annotation succeeds", ->
      annotation.$create.returns(Promise.resolve())
      controller.save()
      assert fakeFlash.error.notCalled

  describe "saving an edited an annotation", ->

    beforeEach ->
      createDirective()
      fakeFlash.error = sandbox.stub()
      controller.action = 'edit'
      annotation.$update = sandbox.stub()

    it "flashes a generic error if the server cannot be reached", (done) ->
      annotation.$update.returns(Promise.reject({status: 0}))

      controller.save().then ->
        assert fakeFlash.error.calledWith(
          "Service unreachable.", "Saving annotation failed")
        done()

    it "flashes an error if saving the annotation fails on the server", (done) ->
      annotation.$update.returns(Promise.reject({
          status: 500,
          statusText: "Server Error",
          data: {}
        })
      )

      controller.save().then ->
        assert fakeFlash.error.calledWith(
          "500 Server Error", "Saving annotation failed")
        done()

    it "doesn't flash an error if saving the annotation succeeds", ->
      annotation.$update.returns(Promise.resolve())

      controller.save()

      assert fakeFlash.error.notCalled

describe("AnnotationController", ->

  before(->
    angular.module("h", [])
    .directive("annotation", require("../annotation"))
  )

  beforeEach(module("h"))

  beforeEach(module("h.templates"))

  # Return Angular's $compile service.
  getCompileService = ->
    $compile = null
    inject((_$compile_) ->
      $compile = _$compile_
    )
    $compile

  # Return Angular's $rootScope.
  getRootScope = ->
    $rootScope = null
    inject((_$rootScope_) ->
      $rootScope = _$rootScope_
    )
    $rootScope

  ###
  Return an annotation directive instance and stub services etc.
  ###
  createAnnotationDirective = ({annotation, personaFilter, momentFilter,
                                urlencodeFilter, drafts, features, flash,
                                permissions, session, tags, time, annotationUI,
                                annotationMapper, groups, documentTitleFilter,
                                documentDomainFilter, localStorage}) ->
    session = session or {state: {userid: "acct:fred@hypothes.is"}}
    locals = {
      personaFilter: personaFilter or ->
      momentFilter: momentFilter or {}
      urlencodeFilter: urlencodeFilter or {}
      drafts: drafts or {
        add: ->
        remove: ->
      }
      features: features or {
        flagEnabled: -> true
      }
      flash: flash or {
        info: ->
        error: ->
      }
      permissions: permissions or {
        isShared: (permissions, group) ->
          return group in permissions.read
        isPrivate: (permissions, user) ->
          return user in permissions.read
        permits: -> true
        shared: (group) -> {"read": [group]}
        private: -> {"read": [session.state.userid]}
      }
      session: session
      tags: tags or {store: ->}
      time: time or {
        toFuzzyString: ->
        nextFuzzyUpdate: ->
      }
      annotationUI: annotationUI or {}
      annotationMapper: annotationMapper or {}
      groups: groups or {
        get: ->
        focused: -> {}
      }
      documentTitleFilter: documentTitleFilter or -> ''
      documentDomainFilter: documentDomainFilter or -> ''
      localStorage: localStorage or {
        setItem: ->
        getItem: ->
      }
    }
    module(($provide) ->
      $provide.value("personaFilter", locals.personaFilter)
      $provide.value("momentFilter", locals.momentFilter)
      $provide.value("urlencodeFilter", locals.urlencodeFilter)
      $provide.value("drafts", locals.drafts)
      $provide.value("features", locals.features)
      $provide.value("flash", locals.flash)
      $provide.value("permissions", locals.permissions)
      $provide.value("session", locals.session)
      $provide.value("tags", locals.tags)
      $provide.value("time", locals.time)
      $provide.value("annotationUI", locals.annotationUI)
      $provide.value("annotationMapper", locals.annotationMapper)
      $provide.value("groups", locals.groups)
      $provide.value("documentTitleFilter", locals.documentTitleFilter)
      $provide.value("documentDomainFilter", locals.documentDomainFilter)
      $provide.value("localStorage", locals.localStorage)
      return
    )

    locals.element = angular.element('<div annotation="annotation">')
    compiledElement = getCompileService()(locals.element)
    locals.$rootScope = getRootScope()
    locals.parentScope = locals.$rootScope.$new()
    locals.parentScope.annotation = annotation or {}
    locals.directive = compiledElement(locals.parentScope)

    locals.$rootScope.$digest()

    locals.controller = locals.element.controller("annotation")
    locals.isolateScope = locals.element.isolateScope()

    locals

  describe("createAnnotationDirective", ->
    it("creates the directive without crashing", ->
      createAnnotationDirective({})
    )

    it("sets the permissions of new annotations from local storage", ->
      {controller} = createAnnotationDirective({
        localStorage: {
          setItem: ->
          getItem: (key) ->
            if key == 'hypothesis.privacy'
              return 'shared'
            else
              assert(false, "Wrong key requested from localStorage")
        }
      })
      assert(controller.isShared())
    )

    it("sets the permissions of new annotations from local storage to private", ->
      {controller} = createAnnotationDirective({
        localStorage: {
          setItem: ->
          getItem: (key) ->
            if key == 'hypothesis.privacy'
              return 'private'
            else
              assert(false, "Wrong key requested from localStorage")
        }
      })
      assert(controller.isPrivate())
    )

    it("defaults to shared if no locally cached visibility", ->
      {controller} = createAnnotationDirective({
        localStorage: {
          setItem: ->
          getItem: ->
        }
      })
      assert(controller.isShared())
    )
  )

  describe("save", ->
    it("Passes group:<id> to the server when saving a new annotation", ->
      annotation = {
        # The annotation needs to have a user or the controller will refuse to
        # save it.
        user: 'acct:fred@hypothes.is'
        # The annotation needs to have some text or it won't validate.
        text: 'foo'
      }
      # Stub $create so we can spy on what gets sent to the server.
      annotation.$create = sinon.stub().returns(Promise.resolve())

      group = {id: "test-id"}

      {controller} = createAnnotationDirective({
        annotation: annotation
        # Mock the groups service, pretend that there's a group with id
        # "test-group" focused.
        groups: {
          focused: -> group
          get: ->
        }
      })
      controller.action = 'create'

      controller.save().then(->
        assert annotation.$create.lastCall.thisValue.group == "test-id"
      )
    )
  )

  ###
  Simulate what happens when the user edits an annotation, clicks Save,
  gets an error because the server fails to save the annotation, then clicks
  Cancel - in the frontend the annotation should be restored to its original
  value, the edits lost.
  ###
  it "restores the original text when editing is cancelled", ->
    {controller} = createAnnotationDirective(
      annotation: {
        id: "test-annotation-id"
        user: "acct:bill@localhost"
        text: "Initial annotation body text"
        # Allow the initial save of the annotation to succeed.
        $create: ->
          Promise.resolve()
        # Simulate saving the edit of the annotation to the server failing.
        $update: ->
          Promise.reject({
            status: 500,
            statusText: "Server Error",
            data: {}
          })
      }
    )

    original_text = controller.annotation.text

    # Simulate the user clicking the Edit button on the annotation.
    controller.edit()

    # Simulate the user typing some text into the annotation editor textarea.
    controller.annotation.text = "changed by test code"

    # Simulate the user hitting the Save button and wait for the
    # (unsuccessful) response from the server.
    controller.save()

    # At this point the annotation editor controls are still open, and the
    # annotation's text is still the modified (unsaved) text.
    assert controller.annotation.text == "changed by test code"

    # Simulate the user clicking the Cancel button.
    controller.revert()

    # Now the original text should be restored.
    assert controller.annotation.text == original_text

    # test that editing reverting changes to an annotation with
    # no text resets the text to be empty
    it "clears the text when reverting changes to a highlight", ->
      {controller} = createAnnotationDirective({
          annotation: {
            id: "test-annotation-id",
            user: "acct:bill@localhost"
          }
      })
      controller.edit()
      assert.equal controller.action, 'edit'
      controller.annotation.text = "this should be reverted"
      controller.revert()
      assert.equal controller.annotation.text, undefined
)
