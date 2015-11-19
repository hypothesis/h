{module, inject} = angular.mock

events = require('../../events')

describe 'annotation', ->
  $compile = null
  $document = null
  $element = null
  $q = null
  $rootScope = null
  $scope = null
  $timeout = null
  $window = null
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
      update: sandbox.stub()
      remove: sandbox.stub()
      get: sandbox.stub()
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
      default: sandbox.stub().returns({read: ['default']})
      setDefault: sandbox.stub()
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
    $provide.value 'groups', fakeGroups
    return

  beforeEach inject (_$compile_, _$document_, _$q_, _$rootScope_, _$timeout_,
                     _$window_) ->
    $compile = _$compile_
    $document = _$document_
    $window = _$window_
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
      $scope.$broadcast(events.USER_CHANGED, {})
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
        assert(fakePermissions.setDefault.calledWithExactly('shared'))
      )

    it 'saves the "private" visibility level to localStorage', ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      controller.edit();
      controller.setPrivacy('private')
      controller.save().then(->
        assert(fakePermissions.setDefault.calledWithExactly('private'))
      )

    it "doesn't save the visibility if the annotation is a reply", ->
      annotation.$update = sinon.stub().returns(Promise.resolve())
      annotation.references = ["parent id"]
      controller.edit();
      controller.setPrivacy('private')
      controller.save().then(->
        assert(not fakePermissions.setDefault.called)
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

  describe '#hasQuotes', ->
    beforeEach ->
      createDirective()

    it 'returns false if the annotation has no quotes', ->
      controller.annotation.target = [{}]
      assert.isFalse(controller.hasQuotes())

    it 'returns true if the annotation has quotes', ->
      controller.annotation.target = [{
        selector: [{
          type: 'TextQuoteSelector'
        }]
      }]
      assert.isTrue(controller.hasQuotes())

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

    describe 'timestamp', ->
      clock = null

      beforeEach ->
        clock = sinon.useFakeTimers()
        annotation.created = (new Date()).toString()
        annotation.updated = (new Date()).toString()

      afterEach ->
        clock.restore()

      it 'is not updated for unsaved annotations', ->
        # Unsaved annotations don't have an updated time yet so a timestamp
        # string can't be computed for them.
        annotation.updated = null
        $scope.$digest()
        assert.equal(controller.timestamp, null)

      it 'is updated on first digest', ->
        $scope.$digest()
        assert.equal(controller.timestamp, 'a while ago')

      it 'is updated after a timeout', ->
        fakeTime.nextFuzzyUpdate.returns(10)
        fakeTime.toFuzzyString.returns('ages ago')
        $scope.$digest()
        clock.tick(11000)
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
    beforeEach ->
      createDirective()
      fakeAnnotationMapper.deleteAnnotation = sandbox.stub()
      fakeFlash.error = sandbox.stub()

    it "calls annotationMapper.delete() if the delete is confirmed", (done) ->
      sandbox.stub($window, 'confirm').returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.resolve())

      controller.delete().then ->
        assert fakeAnnotationMapper.deleteAnnotation.calledWith(annotation)
        done()
      $timeout.flush()

    it "doesn't call annotationMapper.delete() if the delete is cancelled", ->
      sandbox.stub($window, 'confirm').returns(false)
      assert fakeAnnotationMapper.deleteAnnotation.notCalled

    it "flashes a generic error if the server cannot be reached", (done) ->
      sandbox.stub($window, 'confirm').returns(true)
      fakeAnnotationMapper.deleteAnnotation.returns($q.reject({status: 0}))

      controller.delete().then ->
        assert fakeFlash.error.calledWith(
          "Service unreachable.", "Deleting annotation failed")
        done()
      $timeout.flush()

    it "flashes an error if the delete fails on the server", (done) ->
      sandbox.stub($window, 'confirm').returns(true)
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
      sandbox.stub($window, 'confirm').returns(true)
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

  describe "drafts", ->

    it "creates a draft when editing an annotation", ->
      createDirective()
      controller.edit()
      assert.calledWith(fakeDrafts.update, annotation, {
        text: annotation.text,
        tags: annotation.tags,
        permissions: annotation.permissions
      })

    it "starts editing immediately if there is a draft", ->
      fakeDrafts.get.returns({
        tags: [{text: 'unsaved'}]
        text: 'unsaved-text'
      })
      createDirective()
      assert.isTrue(controller.editing)

    it "uses the text and tags from the draft if present", ->
      fakeDrafts.get.returns({
        tags: ['unsaved-tag']
        text: 'unsaved-text'
      })
      createDirective()
      assert.deepEqual(controller.annotation.tags, [{text: 'unsaved-tag'}])
      assert.equal(controller.annotation.text, 'unsaved-text')

    it "removes the draft when changes are discarded", ->
      createDirective()
      controller.edit()
      controller.revert()
      assert.calledWith(fakeDrafts.remove, annotation)

    it "removes the draft when changes are saved", ->
      annotation.$update = sandbox.stub().returns(Promise.resolve())
      createDirective()
      controller.edit()
      controller.save()

      # the controller currently removes the draft whenever an annotation
      # update is committed on the server. This can happen either when saving
      # locally or when an update is committed in another instance of H
      # which is then pushed to the current instance
      annotation.updated = (new Date()).toISOString()
      $scope.$digest()
      assert.calledWith(fakeDrafts.remove, annotation)

  describe "when the focused group changes", ->

    it "updates the current draft", ->
      createDirective()
      controller.edit()
      controller.annotation.text = 'unsaved-text'
      controller.annotation.tags = []
      controller.annotation.permissions = 'new permissions'
      fakeDrafts.get = sinon.stub().returns({text: 'old-draft'})
      fakeDrafts.update = sinon.stub()
      $rootScope.$broadcast(events.GROUP_FOCUSED)
      assert.calledWith(fakeDrafts.update, annotation, {
        text: 'unsaved-text',
        tags: []
        permissions: 'new permissions'
      })

    it "should not create a new draft", ->
      createDirective()
      controller.edit()
      fakeDrafts.update = sinon.stub()
      fakeDrafts.get = sinon.stub().returns(null)
      $rootScope.$broadcast(events.GROUP_FOCUSED)
      assert.notCalled(fakeDrafts.update)

    it "moves new annotations to the focused group", ->
      annotation.id = null
      createDirective()
      fakeGroups.focused = sinon.stub().returns({id: 'new-group'})
      $rootScope.$broadcast(events.GROUP_FOCUSED)
      assert.equal(annotation.group, 'new-group')

   it "updates perms when moving new annotations to the focused group", ->
      # id must be null so that AnnotationController considers this a new
      # annotation.
      annotation.id = null
      annotation.group = 'old-group'
      annotation.permissions = {read: [annotation.group]}

      # This is a shared annotation.
      fakePermissions.isShared.returns(true)
      createDirective()

      # Make permissions.shared() behave like we expect it to.
      fakePermissions.shared = (groupId) ->
        return {read: [groupId]}

      fakeGroups.focused = sinon.stub().returns({id: 'new-group'})
      $rootScope.$broadcast(events.GROUP_FOCUSED)

      assert.deepEqual(annotation.permissions.read, ['new-group'])

   it "saves shared permissions for the new group to drafts", ->
      # id must be null so that AnnotationController considers this a new
      # annotation.
      annotation.id = null
      annotation.group = 'old-group'
      annotation.permissions = {read: [annotation.group]}

      # This is a shared annotation.
      fakePermissions.isShared.returns(true)
      createDirective()

      # drafts.get() needs to return something truthy, otherwise
      # AnnotationController won't try to update the draft for the annotation.
      fakeDrafts.get.returns(true)

      # Make permissions.shared() behave like we expect it to.
      fakePermissions.shared = (groupId) ->
        return {read: [groupId]}

      # Change the focused group.
      fakeGroups.focused = sinon.stub().returns({id: 'new-group'})
      $rootScope.$broadcast(events.GROUP_FOCUSED)

      assert.deepEqual(
        fakeDrafts.update.lastCall.args[1].permissions.read,
        ['new-group'],
        "Shared permissions for the new group should be saved to drafts")

    it "does not change perms when moving new private annotations", ->
      # id must be null so that AnnotationController considers this a new
      # annotation.
      annotation.id = null
      annotation.group = 'old-group'
      annotation.permissions = {read: ['acct:bill@localhost']}
      createDirective()

      # This is a private annotation.
      fakePermissions.isShared.returns(false)

      fakeGroups.focused = sinon.stub().returns({id: 'new-group'})
      $rootScope.$broadcast(events.GROUP_FOCUSED)

      assert.deepEqual(annotation.permissions.read, ['acct:bill@localhost'],
        'The annotation should still be private')


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
        update: ->
        remove: ->
        get: ->
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
        shared: -> {}
        private: -> {}
        default: -> {}
        setDefault: ->
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
  )

  it("sets the user of new annotations", ->
    annotation = {}

    {session} = createAnnotationDirective({annotation: annotation})

    assert.equal(annotation.user, session.state.userid)
  )

  it("sets the permissions of new annotations", ->
    # This is a new annotation, doesn't have any permissions yet.
    annotation = {group: "test-group"}
    permissions = {
      default: sinon.stub().returns("default permissions")
      isShared: ->
      isPrivate: ->
    }

    createAnnotationDirective({
      annotation: annotation, permissions: permissions})

    assert(permissions.default.calledWithExactly("test-group"))
    assert.equal(annotation.permissions, "default permissions",
      "It should set a new annotation's permissions to what
      permissions.default() returns")
  )

  it("doesn't overwrite permissions if the annotation already has them", ->
    # The annotation will already have some permissions, before it's
    # passed to AnnotationController.
    annotation = {
      permissions: {
        read: ["foo"]
        update: ["bar"]
        delete: ["gar"]
        admin: ["har"]
      }
    }
    # Save the original permissions for asserting against later.
    original_permissions = JSON.parse(JSON.stringify(annotation.permissions))
    permissions = {
      default: sinon.stub().returns("new permissions")
      isShared: ->
      isPrivate: ->
    }

    createAnnotationDirective(
      {annotation: annotation, permissions: permissions})

    assert.deepEqual(annotation.permissions, original_permissions)
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

  describe("when the user signs in", ->
    it("sets the user of unsaved annotations", ->
      # This annotation has no user yet, because that's what happens
      # when you create a new annotation while not signed in.
      annotation = {}
      session = {state: {userid: null}}  # Not signed in.

      {$rootScope} = createAnnotationDirective(
        {annotation: annotation, session:session})

      # At this point we would not expect the user to have been set,
      # even though the annotation has been created, because the user isn't
      # signed in.
      assert(!annotation.user)

      # Sign the user in.
      session.state.userid = "acct:fred@hypothes.is"

      # The session service would broadcast USER_CHANGED after sign in.
      $rootScope.$broadcast(events.USER_CHANGED, {})

      assert.equal(annotation.user, session.state.userid)
    )

    it("sets the permissions of unsaved annotations", ->
      # This annotation has no permissions yet, because that's what happens
      # when you create a new annotation while not signed in.
      annotation = {group: "__world__"}
      session = {state: {userid: null}}  # Not signed in.
      permissions = {
        # permissions.default() would return null, because the user isn't
        # signed in.
        default: -> null
        # We just need to mock these two functions so that it doesn't crash.
        isShared: ->
        isPrivate: ->
      }

      {$rootScope} = createAnnotationDirective(
        {annotation: annotation, session:session, permissions: permissions})

      # At this point we would not expect the permissions to have been set,
      # even though the annotation has been created, because the user isn't
      # signed in.
      assert(!annotation.permissions)

      # Sign the user in.
      session.state.userid = "acct:fred@hypothes.is"

      # permissions.default() would now return permissions, because the user
      # is signed in.
      permissions.default = -> "__default_permissions__"

      # The session service would broadcast USER_CHANGED after sign in.
      $rootScope.$broadcast(events.USER_CHANGED, {})

      assert.equal(annotation.permissions, "__default_permissions__")
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
