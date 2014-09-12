assert = chai.assert

describe 'h.directives.annotation', ->
  $scope = null
  annotation = null
  createController = null
  flash = null

  beforeEach module('h.directives')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.annotationGet = (locals) -> annotation
    annotation =
      document:
        title: 'A special document'
      target: [{}]
      uri: 'http://example.com'
    flash = sinon.spy()

    createController = ->
      $controller 'AnnotationController',
        $scope: $scope
        annotator: {plugins: {}, publish: sinon.spy()}
        flash: flash

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

  it 'skips the document object if the annotation has no targets', ->
    annotation.target = []
    controller = createController()
    $scope.$digest()
    assert.isNull(controller.document)
