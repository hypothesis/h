'use strict';

var angular = require('angular');
var proxyquire = require('proxyquire');
var immutable = require('seamless-immutable');

var annotationFixtures = require('./annotation-fixtures');
var events = require('../events');
var util = require('./util');

var unroll = util.unroll;

var fixtures = immutable({
  emptyThread: {
    annotation: undefined,
    children: [],
  },
});

describe('rootThread', function () {
  var fakeAnnotationUI;
  var fakeBuildThread;
  var fakeSearchFilter;
  var fakeViewFilter;

  var $rootScope;

  var rootThread;

  beforeEach(function () {
    fakeAnnotationUI = {
      state: {
        annotations: [],
        expanded: {},
        filterQuery: null,
        focusedAnnotationMap: null,
        forceVisible: {},
        highlighted: [],
        selectedAnnotationMap: null,
        sortKey: 'Location',
        sortKeysAvailable: ['Location'],
        visibleHighlights: false,
      },

      getState: function () {
        return this.state;
      },
      subscribe: sinon.stub(),
      removeAnnotations: sinon.stub(),
      removeSelectedAnnotation: sinon.stub(),
      addAnnotations: sinon.stub(),
      setCollapsed: sinon.stub(),
    };

    fakeBuildThread = sinon.stub().returns(fixtures.emptyThread);

    fakeSearchFilter = {
      generateFacetedFilter: sinon.stub(),
    };

    fakeViewFilter = {
      filter: sinon.stub(),
    };

    angular.module('app', [])
      .value('annotationUI', fakeAnnotationUI)
      .value('searchFilter', fakeSearchFilter)
      .value('viewFilter', fakeViewFilter)
      .service('rootThread', proxyquire('../root-thread', {
        './build-thread': util.noCallThru(fakeBuildThread),
      }));

    angular.mock.module('app');

    angular.mock.inject(function (_$rootScope_, _rootThread_) {
      $rootScope = _$rootScope_;
      rootThread = _rootThread_;
    });
  });

  describe('#thread', function () {
    it('returns the result of buildThread()', function() {
      assert.equal(rootThread.thread(fakeAnnotationUI.state), fixtures.emptyThread);
    });

    it('passes loaded annotations to buildThread()', function () {
      var annotation = annotationFixtures.defaultAnnotation();
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        annotations: [annotation],
      });
      rootThread.thread(fakeAnnotationUI.state);
      assert.calledWith(fakeBuildThread, sinon.match([annotation]));
    });

    it('passes the current selection to buildThread()', function () {
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        selectedAnnotationMap: {id1: true, id2: true},
      });
      rootThread.thread(fakeAnnotationUI.state);
      assert.calledWith(fakeBuildThread, [], sinon.match({
        selected: ['id1', 'id2'],
      }));
    });

    it('passes the current expanded set to buildThread()', function () {
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        expanded: {id1: true, id2: true},
      });
      rootThread.thread(fakeAnnotationUI.state);
      assert.calledWith(fakeBuildThread, [], sinon.match({
        expanded: {id1: true, id2: true},
      }));
    });

    it('passes the current force-visible set to buildThread()', function () {
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        forceVisible: {id1: true, id2: true},
      });
      rootThread.thread(fakeAnnotationUI.state);
      assert.calledWith(fakeBuildThread, [], sinon.match({
        forceVisible: ['id1', 'id2'],
      }));
    });

    it('passes the highlighted set to buildThread()', function () {
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        highlighted: ['id1', 'id2'],
      });
      rootThread.thread(fakeAnnotationUI.state);
      assert.calledWith(fakeBuildThread, [], sinon.match({
        highlighted: ['id1', 'id2'],
      }));
    });
  });

  describe('when the sort order changes', function () {
    function sortBy(annotations, sortCompareFn) {
      return annotations.slice().sort(function (a,b) {
        return sortCompareFn(a,b) ? -1 : sortCompareFn(b,a) ? 1 : 0;
      });
    }

    function targetWithPos(pos) {
      return [{
        selector: [{type: 'TextPositionSelector', start: pos}]
      }];
    }

    unroll('sort order is correct when sorting by #order', function (testCase) {
      var annotations = [{
        target: targetWithPos(1),
        updated: 20,
      },{
        target: targetWithPos(100),
        updated: 100,
      },{
        target: targetWithPos(50),
        updated: 50,
      },{
        target: targetWithPos(20),
        updated: 10,
      }];

      fakeBuildThread.reset();
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state, {
        sortKey: testCase.order,
        sortKeysAvailable: [testCase.order],
      });
      rootThread.thread(fakeAnnotationUI.state);
      var sortCompareFn = fakeBuildThread.args[0][1].sortCompareFn;
      var actualOrder = sortBy(annotations, sortCompareFn).map(function (annot) {
        return annotations.indexOf(annot);
      });
      assert.deepEqual(actualOrder, testCase.expectedOrder);
    }, [
      {order: 'Location', expectedOrder: [0,3,2,1]},
      {order: 'Oldest', expectedOrder: [3,0,2,1]},
      {order: 'Newest', expectedOrder: [1,2,0,3]},
    ]);
  });

  describe('when the filter query changes', function () {
    it('generates a thread filter function from the query', function () {
      fakeBuildThread.reset();
      var filters = [{any: {terms: ['queryterm']}}];
      var annotation = annotationFixtures.defaultAnnotation();
      fakeSearchFilter.generateFacetedFilter.returns(filters);
      fakeAnnotationUI.state = Object.assign({}, fakeAnnotationUI.state,
        {filterQuery: 'queryterm'});
      rootThread.thread(fakeAnnotationUI.state);
      var filterFn = fakeBuildThread.args[0][1].filterFn;

      fakeViewFilter.filter.returns([annotation]);
      assert.equal(filterFn(annotation), true);
      assert.calledWith(fakeViewFilter.filter, sinon.match([annotation]),
        filters);
    });
  });

  context('when annotation events occur', function () {
    var annot = annotationFixtures.defaultAnnotation();

    unroll('removes and reloads annotations when #event event occurs', function (testCase) {
      $rootScope.$broadcast(testCase.event, testCase.annotations);
      var annotations = [].concat(testCase.annotations);
      assert.calledWith(fakeAnnotationUI.removeAnnotations, sinon.match(annotations));
      assert.calledWith(fakeAnnotationUI.addAnnotations, sinon.match(annotations));
    }, [
      {event: events.BEFORE_ANNOTATION_CREATED, annotations: annot},
      {event: events.ANNOTATION_CREATED, annotations: annot},
      {event: events.ANNOTATION_UPDATED, annotations: annot},
      {event: events.ANNOTATIONS_LOADED, annotations: [annot]},
    ]);

    it('expands the parents of new annotations', function () {
      var reply = annotationFixtures.oldReply();
      $rootScope.$broadcast(events.BEFORE_ANNOTATION_CREATED, reply);
      assert.calledWith(fakeAnnotationUI.setCollapsed, reply.references[0], false);
    });

    unroll('removes annotations when #event event occurs', function (testCase) {
      $rootScope.$broadcast(testCase.event, testCase.annotations);
      var annotations = [].concat(testCase.annotations);
      assert.calledWith(fakeAnnotationUI.removeAnnotations, sinon.match(annotations));
    }, [
      {event: events.ANNOTATION_DELETED, annotations: annot},
      {event: events.ANNOTATIONS_UNLOADED, annotations: [annot]},
    ]);

    it('deselects deleted annotations', function () {
      $rootScope.$broadcast(events.ANNOTATION_DELETED, annot);
      assert.calledWith(fakeAnnotationUI.removeSelectedAnnotation, annot);
    });
  });
});
