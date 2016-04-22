'use strict';

var angular = require('angular');
var inherits = require('inherits');
var proxyquire = require('proxyquire');
var EventEmitter = require('tiny-emitter');

var events = require('../events');
var noCallThru = require('./util').noCallThru;

var searchClients;
function FakeSearchClient(resource, opts) {
  assert.ok(resource);
  searchClients.push(this);
  this.cancel = sinon.stub();
  this.incremental = !!opts.incremental;

  this.get = sinon.spy(function (query) {
    assert.ok(query.uri);

    this.emit('results', [{id: query.uri + '123', group: '__world__'}]);
    this.emit('results', [{id: query.uri + '456', group: 'private-group'}]);
    this.emit('end');
  });
}
inherits(FakeSearchClient, EventEmitter);

describe('WidgetController', function () {
  var $rootScope;
  var $scope;
  var fakeAnnotationMapper;
  var fakeAnnotationUI;
  var fakeCrossFrame;
  var fakeDrafts;
  var fakeGroups;
  var fakeRootThread;
  var fakeSettings;
  var fakeStore;
  var fakeStreamer;
  var fakeStreamFilter;
  var sandbox;
  var viewer;

  before(function () {
    angular.module('h', [])
      .controller('WidgetController', proxyquire('../widget-controller',
        noCallThru({
          angular: angular,
          './search-client': FakeSearchClient,
        })
      ));
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
      state: {
        annotations: [{id: '123'}],
        selectedAnnotationMap: {},
      },
      addAnnotations: sandbox.spy(),
      clearSelectedAnnotations: sandbox.spy(),
      hasSelectedAnnotations: function () {
        return !!this.state.selectedAnnotationMap &&
               Object.keys(this.state.selectedAnnotationMap).length > 0;
      },
      getState: function () {
        return this.state;
      },
    };
    fakeCrossFrame = {
      call: sinon.stub(),
      frames: [],
    };
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

    fakeGroups = {
      focused: function () { return {id: 'foo'}; },
      focus: sinon.stub(),
    };

    fakeRootThread = {
      thread: sinon.stub().returns({
        totalChildren: 0,
      }),
      // TODO - Test for usage
      setSearchQuery: sinon.stub(),
      sortBy: sinon.stub(),
    };

    fakeSettings = {
      annotations: 'test',
    };

    fakeStore = {
      SearchResource: {},
    };

    $provide.value('annotationMapper', fakeAnnotationMapper);
    $provide.value('annotationUI', fakeAnnotationUI);
    $provide.value('crossframe', fakeCrossFrame);
    $provide.value('drafts', fakeDrafts);
    $provide.value('rootThread', fakeRootThread);
    $provide.value('store', fakeStore);
    $provide.value('streamer', fakeStreamer);
    $provide.value('streamFilter', fakeStreamFilter);
    $provide.value('groups', fakeGroups);
    $provide.value('settings', fakeSettings);
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
    it('unloads any existing annotations', function () {
      // When new clients connect, all existing annotations should be unloaded
      // before reloading annotations for each currently-connected client
      fakeCrossFrame.frames.push({uri: 'http://example.com/page-a'});
      $scope.$digest();
      fakeAnnotationMapper.unloadAnnotations = sandbox.spy();
      fakeCrossFrame.frames.push({uri: 'http://example.com/page-b'});
      $scope.$digest();
      assert.calledWith(fakeAnnotationMapper.unloadAnnotations,
        fakeAnnotationUI.state.annotations);
    });

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

    context('when there is a selection', function () {
      var uri = 'http://example.com';
      var id = uri + '123';

      beforeEach(function () {
        fakeCrossFrame.frames = [{uri: uri}];
        fakeAnnotationUI.state.selectedAnnotationMap[id] = true;
        $scope.$digest();
      });

      it('selectedAnnotationCount is > 0', function () {
        assert.equal($scope.selectedAnnotationCount(), 1);
      });

      it('switches to the selected annotation\'s group', function () {
        assert.calledWith(fakeGroups.focus, '__world__');
        assert.calledOnce(fakeAnnotationMapper.loadAnnotations);
        assert.calledWith(fakeAnnotationMapper.loadAnnotations, [
          {id: uri + '123', group: '__world__'},
        ]);
      });

      it('fetches annotations for all groups', function () {
        assert.calledWith(searchClients[0].get, {uri: uri, group: null});
      });

      it('loads annotations in one batch', function () {
        assert.notOk(searchClients[0].incremental);
      });
    });

    context('when there is no selection', function () {
      var uri = 'http://example.com';

      beforeEach(function () {
        fakeCrossFrame.frames = [{uri: uri}];
        fakeGroups.focused = function () { return { id: 'a-group' }; };
        $scope.$digest();
      });

      it('selectedAnnotationCount is 0', function () {
        assert.equal($scope.selectedAnnotationCount(), 0);
      });

      it('fetches annotations for the current group', function () {
        assert.calledWith(searchClients[0].get, {uri: uri, group: 'a-group'});
      });

      it('loads annotations in batches', function () {
        assert.ok(searchClients[0].incremental);
      });
    });

    context('when the selected annotation is not available', function () {
      var uri = 'http://example.com';
      var id = uri + 'does-not-exist';

      beforeEach(function () {
        fakeCrossFrame.frames = [{uri: uri}];
        fakeAnnotationUI.state.selectedAnnotationMap[id] = true;
        fakeGroups.focused = function () { return { id: 'private-group' }; };
        $scope.$digest();
      });

      it('loads annotations from the focused group instead', function () {
        assert.calledWith(fakeGroups.focus, 'private-group');
        assert.calledWith(fakeAnnotationMapper.loadAnnotations,
          [{group: "private-group", id: "http://example.com456"}]);
      });
    });
  });

  describe('when an annotation is anchored', function () {
    it('focuses and scrolls to the annotation if already selected', function () {
      var uri = 'http://example.com';
      fakeAnnotationUI.state.selectedAnnotationMap = {'123': true};
      fakeCrossFrame.frames.push({uri: uri});
      var annot = {
        $$tag: 'atag',
        id: '123',
      };
      fakeAnnotationUI.state.annotations = [annot];
      $scope.$digest();
      $rootScope.$broadcast(events.ANNOTATIONS_SYNCED, [{tag: 'atag'}]);
      assert.calledWith(fakeCrossFrame.call, 'focusAnnotations', ['atag']);
      assert.calledWith(fakeCrossFrame.call, 'scrollToAnnotation', 'atag');
    });
  });

  describe('when the focused group changes', function () {
    it('should load annotations for the new group', function () {
      var uri = 'http://example.com';
      fakeCrossFrame.frames.push({uri: uri});
      var loadSpy = fakeAnnotationMapper.loadAnnotations;

      $scope.$broadcast(events.GROUP_FOCUSED);
      assert.calledWith(fakeAnnotationMapper.unloadAnnotations, [{id: '123'}]);
      assert.calledWith(fakeAnnotationUI.addAnnotations, fakeDrafts.unsaved());
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

  describe('direct linking messages', function () {
    it('displays a message if the selection is unavailable', function () {
      fakeAnnotationUI.state.selectedAnnotationMap = {'missing': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isTrue($scope.selectedAnnotationUnavailable());
    });

    it('does not show a message if the selection is available', function () {
      fakeAnnotationUI.state.selectedAnnotationMap = {'123': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isFalse($scope.selectedAnnotationUnavailable());
    });

    it('does not a show a message if there is no selection', function () {
      fakeAnnotationUI.state.selectedAnnotationMap = null;
      $scope.$digest();
      assert.isFalse($scope.selectedAnnotationUnavailable());
    });

    it('shows logged out message if selection is available', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      fakeAnnotationUI.state.selectedAnnotationMap = {'123': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isTrue($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if selection is unavailable', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      fakeAnnotationUI.state.selectedAnnotationMap = {'missing': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if there is no selection', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      fakeAnnotationUI.state.selectedAnnotationMap = null;
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if user is not logged out', function () {
      $scope.auth = {
        status: 'signed-in'
      };
      fakeAnnotationUI.state.selectedAnnotationMap = {'123': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if not a direct link', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      delete fakeSettings.annotations;
      fakeAnnotationUI.state.selectedAnnotationMap = {'123': true};
      fakeAnnotationUI.state.annotations = [{id: '123'}];
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });
  });
});
