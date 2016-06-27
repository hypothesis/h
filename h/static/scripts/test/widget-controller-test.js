'use strict';

var angular = require('angular');
var inherits = require('inherits');
var proxyquire = require('proxyquire');
var EventEmitter = require('tiny-emitter');

var annotationUIFactory = require('../annotation-ui');
var events = require('../events');
var noCallThru = require('./util').noCallThru;

var searchClients;
function FakeSearchClient(searchFn, opts) {
  assert.ok(searchFn);
  searchClients.push(this);
  this.cancel = sinon.stub();
  this.incremental = !!opts.incremental;

  this.get = sinon.spy(function (query) {
    assert.ok(query.uri);

    for (var i = 0; i < query.uri.length; i++) {
      var uri = query.uri[i];
      this.emit('results', [{id: uri + '123', group: '__world__'}]);
      this.emit('results', [{id: uri + '456', group: 'private-group'}]);
    }

    this.emit('end');
  });
}
inherits(FakeSearchClient, EventEmitter);

function FakeRootThread() {
  this.thread = sinon.stub().returns({
    totalChildren: 0,
  });
}
inherits(FakeRootThread, EventEmitter);

function FakeVirtualThreadList() {
  this.setRootThread = sinon.stub();
  this.setThreadHeight = sinon.stub();
  this.detach = sinon.stub();
  this.yOffsetOf = function () {
    return 100;
  };
}
inherits(FakeVirtualThreadList, EventEmitter);

describe('WidgetController', function () {
  var $rootScope;
  var $scope;
  var annotationUI;
  var fakeAnnotationMapper;
  var fakeCrossFrame;
  var fakeDrafts;
  var fakeFeatures;
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

    annotationUI = annotationUIFactory({});

    fakeCrossFrame = {
      call: sinon.stub(),
      frames: [],
    };

    fakeDrafts = {
      unsaved: sandbox.stub().returns([]),
    };

    fakeFeatures = {
      flagEnabled: sandbox.stub().returns(true),
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

    fakeRootThread = new FakeRootThread();

    fakeSettings = {
      annotations: 'test',
    };

    fakeStore = {
      search: sinon.stub(),
    };

    $provide.value('VirtualThreadList', FakeVirtualThreadList);
    $provide.value('annotationMapper', fakeAnnotationMapper);
    $provide.value('annotationUI', annotationUI);
    $provide.value('crossframe', fakeCrossFrame);
    $provide.value('drafts', fakeDrafts);
    $provide.value('features', fakeFeatures);
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
      annotationUI.addAnnotations([{id: '123'}]);
      var uri1 = 'http://example.com/page-a';
      fakeCrossFrame.frames.push({uri: uri1, searchUris: [uri1]});
      $scope.$digest();
      fakeAnnotationMapper.unloadAnnotations = sandbox.spy();
      var uri2 = 'http://example.com/page-b';
      fakeCrossFrame.frames.push({uri: uri2, searchUris: [uri2]});
      $scope.$digest();
      assert.calledWith(fakeAnnotationMapper.unloadAnnotations,
        annotationUI.getState().annotations);
    });

    it('loads all annotations for a frame', function () {
      var uri = 'http://example.com';
      fakeCrossFrame.frames.push({uri: uri, searchUris: [uri]});
      $scope.$digest();
      var loadSpy = fakeAnnotationMapper.loadAnnotations;
      assert.calledWith(loadSpy, [sinon.match({id: uri + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uri + '456'})]);
    });

    it('loads all annotations for a frame with multiple urls', function () {
      var uri = 'http://example.com/test.pdf';
      var fingerprint = 'urn:x-pdf:fingerprint';
      fakeCrossFrame.frames.push({uri: uri, searchUris: [uri, fingerprint]});
      $scope.$digest();
      var loadSpy = fakeAnnotationMapper.loadAnnotations;
      assert.calledWith(loadSpy, [sinon.match({id: uri + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: fingerprint + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uri + '456'})]);
      assert.calledWith(loadSpy, [sinon.match({id: fingerprint + '456'})]);
    });

    it('loads all annotations for all frames', function () {
      var uris = ['http://example.com', 'http://foobar.com'];
      fakeCrossFrame.frames = uris.map(function (uri) {
        return {uri: uri, searchUris: [uri]};
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
        fakeCrossFrame.frames = [{uri: uri, searchUris: [uri]}];
        annotationUI.selectAnnotations([id]);
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
        assert.calledWith(searchClients[0].get, {uri: [uri], group: null});
      });

      it('loads annotations in one batch', function () {
        assert.notOk(searchClients[0].incremental);
      });
    });

    context('when there is no selection', function () {
      var uri = 'http://example.com';

      beforeEach(function () {
        fakeCrossFrame.frames = [{uri: uri, searchUris: [uri]}];
        fakeGroups.focused = function () { return { id: 'a-group' }; };
        $scope.$digest();
      });

      it('selectedAnnotationCount is 0', function () {
        assert.equal($scope.selectedAnnotationCount(), 0);
      });

      it('fetches annotations for the current group', function () {
        assert.calledWith(searchClients[0].get, {uri: [uri], group: 'a-group'});
      });

      it('loads annotations in batches', function () {
        assert.ok(searchClients[0].incremental);
      });
    });

    context('when the selected annotation is not available', function () {
      var uri = 'http://example.com';
      var id = uri + 'does-not-exist';

      beforeEach(function () {
        fakeCrossFrame.frames = [{uri: uri, searchUris: [uri]}];
        annotationUI.selectAnnotations([id]);
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
      annotationUI.selectAnnotations(['123']);
      fakeCrossFrame.frames.push({uri: uri, searchUris: [uri]});
      var annot = {
        $$tag: 'atag',
        id: '123',
      };
      annotationUI.addAnnotations([annot]);
      $scope.$digest();
      $rootScope.$broadcast(events.ANNOTATIONS_SYNCED, [{tag: 'atag'}]);
      assert.calledWith(fakeCrossFrame.call, 'focusAnnotations', ['atag']);
      assert.calledWith(fakeCrossFrame.call, 'scrollToAnnotation', 'atag');
    });
  });

  describe('when the focused group changes', function () {
    it('should load annotations for the new group', function () {
      var uri = 'http://example.com';

      annotationUI.addAnnotations([{id: '123'}]);
      annotationUI.addAnnotations = sinon.stub();

      fakeDrafts.unsaved.returns([{id: uri + '123'}, {id: uri + '456'}]);

      fakeCrossFrame.frames.push({uri: uri, searchUris: [uri]});
      var loadSpy = fakeAnnotationMapper.loadAnnotations;

      $scope.$broadcast(events.GROUP_FOCUSED);
      assert.calledWith(fakeAnnotationMapper.unloadAnnotations, [{id: '123'}]);
      assert.calledWith(annotationUI.addAnnotations, fakeDrafts.unsaved());
      $scope.$digest();
      assert.calledWith(loadSpy, [sinon.match({id: uri + '123'})]);
      assert.calledWith(loadSpy, [sinon.match({id: uri + '456'})]);
    });
  });

  describe('when a new annotation is created', function () {
    var windowScroll;

    beforeEach(function () {
      $scope.clearSelection = sinon.stub();
      windowScroll = sinon.stub(window, 'scroll');
    });

    afterEach(function () {
      windowScroll.restore();
    });

    /**
     *  It should clear any selection that exists in the sidebar before
     *  creating a new annotation. Otherwise the new annotation with its
     *  form open for the user to type in won't be visible because it's
     *  not part of the selection.
     */
    it('clears the selection', function () {
      $rootScope.$emit('beforeAnnotationCreated', {});
      assert.called($scope.clearSelection);
    });

    it('does not clear the selection if the new annotation is a highlight', function () {
      $rootScope.$emit('beforeAnnotationCreated', {$highlight: true});
      assert.notCalled($scope.clearSelection);
    });

    it('does not clear the selection if the new annotation is a reply', function () {
      $rootScope.$emit('beforeAnnotationCreated', {
        references: ['parent-id']
      });
      assert.notCalled($scope.clearSelection);
    });

    it('scrolls the viewport to the new annotation', function () {
      $rootScope.$emit('beforeAnnotationCreated', {$$tag: '123'});
      assert.called(windowScroll);
    });
  });

  describe('direct linking messages', function () {

    beforeEach(function () {
      // The document has finished loading.
      fakeCrossFrame.frames = [
        {
          uri: 'http://www.example.com',
          searchUris: [],
        }
      ];
    });

    it('displays a message if the selection is unavailable', function () {
      annotationUI.selectAnnotations(['missing']);
      $scope.$digest();
      assert.isTrue($scope.selectedAnnotationUnavailable());
    });

    it('does not show a message if the selection is available', function () {
      annotationUI.addAnnotations([{id: '123'}]);
      annotationUI.selectAnnotations(['123']);
      $scope.$digest();
      assert.isFalse($scope.selectedAnnotationUnavailable());
    });

    it('does not a show a message if there is no selection', function () {
      annotationUI.selectAnnotations([]);
      $scope.$digest();
      assert.isFalse($scope.selectedAnnotationUnavailable());
    });

    it("doesn't show a message if the document isn't loaded yet", function () {
      // No search requests have been sent yet.
      searchClients = [];
      // There is a selection but the selected annotation isn't available.
      annotationUI.selectAnnotations(['missing']);
      // The document hasn't finished loading.
      fakeCrossFrame.frames = [];
      $scope.$digest();

      assert.isFalse($scope.selectedAnnotationUnavailable());
    });

    it('shows logged out message if selection is available', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      annotationUI.addAnnotations([{id: '123'}]);
      annotationUI.selectAnnotations(['123']);
      $scope.$digest();
      assert.isTrue($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if selection is unavailable', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      annotationUI.selectAnnotations(['missing']);
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if there is no selection', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      annotationUI.selectAnnotations([]);
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if user is not logged out', function () {
      $scope.auth = {
        status: 'signed-in'
      };
      annotationUI.addAnnotations([{id: '123'}]);
      annotationUI.selectAnnotations(['123']);
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });

    it('does not show loggedout message if not a direct link', function () {
      $scope.auth = {
        status: 'signed-out'
      };
      delete fakeSettings.annotations;
      annotationUI.addAnnotations([{id: '123'}]);
      annotationUI.selectAnnotations(['123']);
      $scope.$digest();
      assert.isFalse($scope.shouldShowLoggedOutMessage());
    });
  });

  describe('#forceVisible', function () {
    it('shows the thread', function () {
      var thread = {id: '1'};
      $scope.forceVisible(thread);
      assert.deepEqual(annotationUI.getState().forceVisible, {1: true});
    });

    it('uncollapses the parent', function () {
      var thread = {
        id: '2',
        parent: {id: '3'},
      };
      assert.equal(annotationUI.getState().expanded[thread.parent.id], undefined);
      $scope.forceVisible(thread);
      assert.equal(annotationUI.getState().expanded[thread.parent.id], true);
    });
  });

  describe('#visibleCount', function () {
    it('returns the total number of visible annotations or replies', function () {
      fakeRootThread.thread.returns({
        children: [{
          id: '1',
          visible: true,
          children: [{ id: '3', visible: true, children: [] }],
        },{
          id: '2',
          visible: false,
          children: [],
        }],
      });
      $scope.$digest();
      assert.equal($scope.visibleCount(), 2);
    });
  });
});
