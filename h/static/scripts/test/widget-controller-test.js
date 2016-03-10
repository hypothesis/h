'use strict';

var angular = require('angular');
var inherits = require('inherits');
var proxyquire = require('proxyquire');
var EventEmitter = require('tiny-emitter');

var events = require('../events');

function noCallThru(stub) {
  return Object.assign(stub, {'@noCallThru':true});
}

var searchClients;
function FakeSearchClient(resource) {
  assert.ok(resource);
  searchClients.push(this);
  this.cancel = sinon.stub();

  this.get = function (query) {
    assert.ok(query.uri);
    this.emit('results', [{id: query.uri + '123', group: '__world__'}]);
    this.emit('results', [{id: query.uri + '456', group: 'private-group'}]);
    this.emit('end');
  };
}
inherits(FakeSearchClient, EventEmitter);

describe('WidgetController', function () {
  var $scope = null;
  var $rootScope = null;
  var fakeAnnotationMapper = null;
  var fakeAnnotationUI = null;
  var fakeCrossFrame = null;
  var fakeDrafts = null;
  var fakeStore = null;
  var fakeStreamer = null;
  var fakeStreamFilter = null;
  var fakeThreading = null;
  var fakeGroups = null;
  var sandbox = null;
  var viewer = null;

  before(function () {
    angular.module('h', [])
      .controller('WidgetController', proxyquire('../widget-controller', {
        angular: noCallThru(angular),
        './search-client': noCallThru(FakeSearchClient),
      }));
  });

  beforeEach(angular.mock.module('h'));

  beforeEach(angular.mock.module(function ($provide) {
    searchClients = [];
    sandbox = sinon.sandbox.create();

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy(),
      unloadAnnotations: sandbox.spy()
    };

    fakeAnnotationUI = {
      clearSelectedAnnotations: sandbox.spy(),
      selectedAnnotationMap: {},
      hasSelectedAnnotations: function () {
        return Object.keys(this.selectedAnnotationMap).length > 0;
      },
    };
    fakeCrossFrame = {frames: []};
    fakeDrafts = {
      unsaved: sandbox.stub()
    };

    fakeStreamer = {
      setConfig: sandbox.spy()
    };

    fakeStreamFilter = {
      resetFilter: sandbox.stub().returnsThis(),
      addClause: sandbox.stub().returnsThis(),
      getFilter: sandbox.stub().returns({})
    };

    fakeThreading = {
      root: {},
      thread: sandbox.stub(),
      annotationList: function () {
        return [{id: '123'}];
      },
    };

    fakeGroups = {
      focused: function () { return {id: 'foo'}; },
      focus: sinon.stub(),
    };

    fakeStore = {
      SearchResource: {},
    };

    $provide.value('annotationMapper', fakeAnnotationMapper);
    $provide.value('annotationUI', fakeAnnotationUI);
    $provide.value('crossframe', fakeCrossFrame);
    $provide.value('drafts', fakeDrafts);
    $provide.value('store', fakeStore);
    $provide.value('streamer', fakeStreamer);
    $provide.value('streamFilter', fakeStreamFilter);
    $provide.value('threading', fakeThreading);
    $provide.value('groups', fakeGroups);
  }));

  beforeEach(angular.mock.inject(function ($controller, _$rootScope_) {
    $rootScope = _$rootScope_;
    $scope = $rootScope.$new();
    viewer = $controller('WidgetController', {$scope: $scope});
  }));

  afterEach(function () {
    return sandbox.restore();
  });

  describe('loadAnnotations', function () {
    it('loads all annotations for a frame', function () {
      var uri = 'http://example.com';
      fakeCrossFrame.frames.push({uri: uri});
      $scope.$digest();
      var loadSpy = fakeAnnotationMapper.loadAnnotations;
      assert.calledWith(loadSpy, [sinon.match({id: uri + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uri + '456'})]);
    });

    it('loads all annotations for all frames', function () {
      var uris = ['http://example.com', 'http://foobar.com'];
      fakeCrossFrame.frames = uris.map(function (uri) {
        return {uri: uri};
      });
      $scope.$digest();
      var loadSpy = fakeAnnotationMapper.loadAnnotations;
      assert.calledWith(loadSpy, [sinon.match({id: uris[0] + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uris[0] + '456'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uris[1] + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uris[1] + '456'})]);
    });
  });

  describe('when the focused group changes', function () {
    it('should load annotations for the new group', function () {
      var uri = 'http://example.com';
      fakeCrossFrame.frames.push({uri: uri});
      var loadSpy = fakeAnnotationMapper.loadAnnotations;

      $scope.$broadcast(events.GROUP_FOCUSED);
      assert.calledWith(fakeAnnotationMapper.unloadAnnotations, [{id: '123'}]);
      assert.calledWith(fakeThreading.thread, fakeDrafts.unsaved());
      $scope.$digest();
      assert.calledWith(loadSpy, [sinon.match({id: uri + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uri + '456'})]);
    });
  });

  describe('when a new annotation is created', function () {
    /**
     *  It should clear any selection that exists in the sidebar before
     *  creating a new annotation. Otherwise the new annotation with its
     *  form open for the user to type in won't be visible because it's
     *  not part of the selection.
     */
    it('clears the selection', function () {
      $scope.clearSelection = sinon.stub();
      $rootScope.$emit('beforeAnnotationCreated', {});
      assert.called($scope.clearSelection);
    });

    it('does not clear the selection if the new annotation is a highlight', function () {
      $scope.clearSelection = sinon.stub();
      $rootScope.$emit('beforeAnnotationCreated', {$highlight: true});
      assert.notCalled($scope.clearSelection);
    });

    it('does not clear the selection if the new annotation is a reply', function () {
      $scope.clearSelection = sinon.stub();
      $rootScope.$emit('beforeAnnotationCreated', {
        references: ['parent-id']
      });
      assert.notCalled($scope.clearSelection);
    });
  });
});
