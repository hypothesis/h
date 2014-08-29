assert = chai.assert

describe 'h.directives.annotation', ->
  $scope = null
  annotation = null
  createController = null

  beforeEach module('h.directives.annotation')

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.model =
      document:
        title: 'A special document'
      target: [{}]
      uri: 'http://example.com'

    createController = ->
      $controller 'AnnotationController',
        $scope: $scope
        $element: null
        $location: {}
        $rootScope: $rootScope
        $sce: null
        $timeout: sinon.spy()
        $window: {}
        annotator: {plugins: {}}
        documentHelpers: {baseURI: '', absoluteURI: sinon.spy()}
        drafts: null

  it 'provides a document title', ->
    controller = createController()
    assert.equal($scope.document.title, 'A special document')

  it 'truncates long titles', ->
    $scope.model.document.title = '''A very very very long title that really
    shouldn't be found on a page on the internet.'''
    controller = createController()
    assert.equal($scope.document.title, 'A very very very long title th…')

  it 'provides a document uri', ->
    controller = createController()
    assert.equal($scope.document.uri, 'http://example.com')

  it 'provides an extracted domain from the uri', ->
    controller = createController()
    assert.equal($scope.document.domain, 'example.com')

  it 'uses the domain for the title if the title is not present', ->
    delete $scope.model.document.title
    controller = createController()
    assert.equal($scope.document.title, 'example.com')

  it 'skips the document object if no document is present on the annotation', ->
    delete $scope.model.document
    controller = createController()
    assert.isUndefined($scope.document)

  it 'skips the document object if the annotation has no targets', ->
    $scope.model.target = []
    controller = createController()
    assert.isUndefined($scope.document)
