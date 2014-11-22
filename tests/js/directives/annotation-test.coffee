assert = chai.assert
sandbox = sinon.sandbox.create()

describe 'h.directives.annotation', ->
  $scope = null
  annotator = null
  annotation = null
  createController = null
  flash = null

  beforeEach module('h')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.annotationGet = (locals) -> annotation
    annotator = {plugins: {}, publish: sandbox.spy()}
    annotation =
      id: 'deadbeef'
      document:
        title: 'A special document'
      target: [{}]
      uri: 'http://example.com'
    flash = sinon.spy()

    createController = ->
      $controller 'AnnotationController',
        $scope: $scope
        annotator: annotator
        flash: flash

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

      annotator.publish = sinon.spy (event, ann) ->
        return unless event == 'beforeAnnotationCreated'
        ann.permissions =
          read: ['acct:bill@localhost']
          update: ['acct:bill@localhost']
          destroy: ['acct:bill@localhost']
          admin: ['acct:bill@localhost']

    it 'creates a new reply with the proper uri and references', ->
      controller.reply()
      match = sinon.match {references: [annotation.id], uri: annotation.uri}
      assert.calledWith(annotator.publish, 'beforeAnnotationCreated', match)

    it 'adds the world readable principal if the parent is public', ->
      annotation.permissions.read.push('group:__world__')
      controller.reply()
      newAnnotation = annotator.publish.lastCall.args[1]
      assert.include(newAnnotation.permissions.read, 'group:__world__')

    it 'does not add the world readable principal if the parent is privace', ->
      controller.reply()
      newAnnotation = annotator.publish.lastCall.args[1]
      assert.notInclude(newAnnotation.permissions.read, 'group:__world__')

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
