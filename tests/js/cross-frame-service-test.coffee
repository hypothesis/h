assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'CrossFrameService', ->
  sandbox = sinon.sandbox.create()
  $rootScope = null
  $fakeDocument = null
  $fakeWindow = null
  fakeStore = null
  fakeAnnotationUI = null

  beforeEach module('h')
  beforeEach module ($provide) ->
    $fakeDocument = {}
    $fakeWindow = {}
    fakeStore = {}
    fakeAnnotationUI = {}

    $provide.value('$document', $fakeDocument)
    $provide.value('$window', $fakeWindow)
    $provide.value('store', fakeStore)
    $provide.value('annotationUI', fakeAnnotationUI)

  beforeEach inject (_$rootScope_, _crossframe_) ->
    $rootScope = _$rootScope_
    crossframe = _crossframe_

  afterEach ->
    sandbox.restore()

  describe '.connect()', ->
  describe '.notify()', ->
    it 'proxies the call to the bridge'
