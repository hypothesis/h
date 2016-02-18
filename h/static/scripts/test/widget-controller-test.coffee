{module, inject} = angular.mock

events = require('../events')

describe 'WidgetController', ->
  $scope = null
  $rootScope = null
  fakeAnnotationMapper = null
  fakeAnnotationUI = null
  fakeAuth = null
  fakeCrossFrame = null
  fakeDrafts = null
  fakeStore = null
  fakeStreamer = null
  fakeStreamFilter = null
  fakeThreading = null
  fakeGroups = null
  lastSearchResult = null
  sandbox = null
  viewer = null

  before ->
    angular.module('h', [])
    .controller('WidgetController', require('../widget-controller.coffee'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy()
      unloadAnnotations: sandbox.spy()
    }

    fakeAnnotationUI = {
      tool: 'comment'
      clearSelectedAnnotations: sandbox.spy()
    }
    fakeAuth = {user: null}
    fakeCrossFrame = {frames: []}
    fakeDrafts = {
      unsaved: sandbox.stub()
    }

    fakeStore = {
      SearchResource:
        get: (query, callback) ->
          offset = query.offset or 0
          limit = query.limit or 20
          result =
            total: 100
            rows: [offset..offset+limit-1]
            replies: []
          callback result
    }

    fakeStreamer = {
      setConfig: sandbox.spy()
    }

    fakeStreamFilter = {
      resetFilter: sandbox.stub().returnsThis()
      addClause: sandbox.stub().returnsThis()
      getFilter: sandbox.stub().returns({})
    }

    fakeThreading = {
      root: {},
      thread: sandbox.stub()
    }

    fakeGroups = {
      focused: -> {id: 'foo'}
    }

    $provide.value 'annotationMapper', fakeAnnotationMapper
    $provide.value 'annotationUI', fakeAnnotationUI
    $provide.value 'crossframe', fakeCrossFrame
    $provide.value 'drafts', fakeDrafts
    $provide.value 'store', fakeStore
    $provide.value 'streamer', fakeStreamer
    $provide.value 'streamFilter', fakeStreamFilter
    $provide.value 'threading', fakeThreading
    $provide.value 'groups', fakeGroups
    return

  beforeEach inject ($controller, _$rootScope_) ->
    $rootScope = _$rootScope_
    $scope = $rootScope.$new()
    viewer = $controller 'WidgetController', {$scope}

  afterEach ->
    sandbox.restore()

  describe 'loadAnnotations', ->
    it 'loads all annotations for a frame', ->
      viewer.chunkSize = 20
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$digest()
      loadSpy = fakeAnnotationMapper.loadAnnotations
      assert.callCount(loadSpy, 5)
      assert.calledWith(loadSpy, [0..19])
      assert.calledWith(loadSpy, [20..39])
      assert.calledWith(loadSpy, [40..59])
      assert.calledWith(loadSpy, [60..79])
      assert.calledWith(loadSpy, [80..99])

    it 'passes _separate_replies: true to the search API', ->
      fakeStore.SearchResource.get = sandbox.stub()
      fakeCrossFrame.frames.push({uri: 'http://example.com'})

      $scope.$digest()

      assert.equal(
        fakeStore.SearchResource.get.firstCall.args[0]._separate_replies, true)

    it 'passes annotations and replies from search to loadAnnotations()', ->
      fakeStore.SearchResource.get = (query, callback) ->
        callback({
          rows: ['annotation_1', 'annotation_2']
          replies: ['reply_1', 'reply_2', 'reply_3']
        })
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      $scope.$digest()

      assert fakeAnnotationMapper.loadAnnotations.calledOnce
      assert fakeAnnotationMapper.loadAnnotations.calledWith(
        ['annotation_1', 'annotation_2'], ['reply_1', 'reply_2', 'reply_3']
      )

  describe 'when the focused group changes', ->
    it 'should load annotations for the new group', ->
      fakeThreading.annotationList = sandbox.stub().returns([{id: '1'}])
      fakeCrossFrame.frames.push({uri: 'http://example.com'})
      searchResult = {total: 10, rows: [0..10], replies: []}
      fakeStore.SearchResource.get = (query, callback) ->
        callback(searchResult)

      $scope.$broadcast(events.GROUP_FOCUSED)

      assert.calledWith(fakeAnnotationMapper.unloadAnnotations,
        [{id: '1'}])
      $scope.$digest();
      assert.calledWith(fakeAnnotationMapper.loadAnnotations,
        searchResult.rows)
      assert.calledWith(fakeThreading.thread, fakeDrafts.unsaved())

  describe 'when a new annotation is created', ->
    ###*
    #  It should clear any selection that exists in the sidebar before
    #  creating a new annotation. Otherwise the new annotation with its
    #  form open for the user to type in won't be visible because it's
    #  not part of the selection.
    ###
    it 'clears the selection', ->
      $scope.clearSelection = sinon.stub()
      $rootScope.$emit('beforeAnnotationCreated', {})
      assert.called($scope.clearSelection)

    it 'does not clear the selection if the new annotation is a highlight', ->
      $scope.clearSelection = sinon.stub()
      $rootScope.$emit('beforeAnnotationCreated', {$highlight: true})
      assert.notCalled($scope.clearSelection)

    it 'does not clear the selection if the new annotation is a reply', ->
      $scope.clearSelection = sinon.stub()
      $rootScope.$emit('beforeAnnotationCreated', {
        references: ['parent-id']
      })
      assert.notCalled($scope.clearSelection)
