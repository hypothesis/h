'use strict';

var angular = require('angular');

var events = require('../events');

describe('WidgetController', function () {
  var $scope = null;
  var $rootScope = null;
  var fakeAnnotationMapper = null;
  var fakeAnnotationUI = null;
  var fakeAuth = null;
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
      .controller('WidgetController', require('../widget-controller'));
  });

  beforeEach(angular.mock.module('h'));

  beforeEach(angular.mock.module(function ($provide) {
    sandbox = sinon.sandbox.create();

    fakeAnnotationMapper = {
      loadAnnotations: sandbox.spy(),
      unloadAnnotations: sandbox.spy()
    };

    fakeAnnotationUI = {
      tool: 'comment',
      clearSelectedAnnotations: sandbox.spy()
    };
    fakeAuth = {user: null};
    fakeCrossFrame = {frames: []};
    fakeDrafts = {
      unsaved: sandbox.stub()
    };

    fakeStore = {
      SearchResource: {
        get: function (query, callback) {
          var offset = query.offset || 0;
          var limit = query.limit || 20;
          var result =
            {
              total: 100,
              rows: ((function () {
                var result1 = [];
                var end = offset + limit - 1;
                var i = offset;
                if (offset <= end) {
                  while (i <= end) {
                    result1.push(i++);
                  }
                } else {
                  while (i >= end) {
                    result1.push(i--);
                  }
                }
                return result1;
              })()),
              replies: []
            };
          return callback(result);
        }
      },
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
      thread: sandbox.stub()
    };

    fakeGroups = {
      focused: function () { return {id: 'foo'}; }
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
    return;
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
      $scope.chunkSize = 20;
      fakeCrossFrame.frames.push({uri: 'http://example.com'});
      $scope.$digest();
      var loadSpy = fakeAnnotationMapper.loadAnnotations;
      assert.callCount(loadSpy, 5);
      assert.calledWith(loadSpy, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]);
      assert.calledWith(loadSpy, [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]);
      assert.calledWith(loadSpy, [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]);
      assert.calledWith(loadSpy, [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]);
      assert.calledWith(loadSpy, [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99]);
    });

    it('passes _separate_replies: true to the search API', function () {
      fakeStore.SearchResource.get = sandbox.stub();
      fakeCrossFrame.frames.push({uri: 'http://example.com'});

      $scope.$digest();

      assert.equal(
        fakeStore.SearchResource.get.firstCall.args[0]._separate_replies, true);
    });

    return it('passes annotations and replies from search to loadAnnotations()', function () {
      fakeStore.SearchResource.get = function (query, callback) {
        return callback({
          rows: ['annotation_1', 'annotation_2'],
          replies: ['reply_1', 'reply_2', 'reply_3']
        });
      };
      fakeCrossFrame.frames.push({uri: 'http://example.com'});
      $scope.$digest();

      assert(fakeAnnotationMapper.loadAnnotations.calledOnce);
      assert(fakeAnnotationMapper.loadAnnotations.calledWith(
        ['annotation_1', 'annotation_2'], ['reply_1', 'reply_2', 'reply_3']
      ));
    });
  });

  describe('when the focused group changes', function () {
    return it('should load annotations for the new group', function () {
      fakeThreading.annotationList = sandbox.stub().returns([{id: '1'}]);
      fakeCrossFrame.frames.push({uri: 'http://example.com'});
      var searchResult = {total: 10, rows: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], replies: []};
      fakeStore.SearchResource.get = function (query, callback) {
        return callback(searchResult);
      };

      $scope.$broadcast(events.GROUP_FOCUSED);

      assert.calledWith(fakeAnnotationMapper.unloadAnnotations, [{id: '1'}]);
      $scope.$digest();
      assert.calledWith(fakeAnnotationMapper.loadAnnotations, searchResult.rows);
      assert.calledWith(fakeThreading.thread, fakeDrafts.unsaved());
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
