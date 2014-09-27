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

  it 'provides a document title', ->
    controller = createController()
    $scope.$digest()
    assert.equal(controller.document.title, 'A special document')

  it 'truncates long titles', ->
    annotation.document.title = '''A very very very long title that really
    shouldn't be found on a page on the internet.'''
    controller = createController()
    $scope.$digest()
    assert.equal(controller.document.title, 'A very very very long title th…')

  it 'provides a document uri', ->
    controller = createController()
    $scope.$digest()
    assert.equal(controller.document.uri, 'http://example.com')

  it 'provides an extracted domain from the uri', ->
    controller = createController()
    $scope.$digest()
    assert.equal(controller.document.domain, 'example.com')

  it 'uses the domain for the title if the title is not present', ->
    delete annotation.document.title
    controller = createController()
    $scope.$digest()
    assert.equal(controller.document.title, 'example.com')

  it 'skips the document object if no document is present on the annotation', ->
    delete annotation.document
    controller = createController()
    $scope.$digest()
    assert.isNull(controller.document)

  describe '#reply', ->
    controller = null
    container = null

    beforeEach ->
      controller = createController()

    it 'creates a new reply with the proper uri and references', ->
      controller.reply()
      match = sinon.match {references: [annotation.id], uri: annotation.uri}
      assert.calledWith(annotator.publish, 'beforeAnnotationCreated', match)
