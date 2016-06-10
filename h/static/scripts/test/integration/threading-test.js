'use strict';

var angular = require('angular');
var immutable = require('seamless-immutable');

var unroll = require('../util').unroll;

var fixtures = immutable({
  annotations: [{
    id: '1',
    references: [],
    text: 'first annotation',
    updated: 50,
  },{
    id: '2',
    references: [],
    text: 'second annotation',
    updated: 200,
  },{
    id: '3',
    references: ['2'],
    text: 'reply to first annotation',
    updated: 100,
  }],
});

describe('annotation threading', function () {
  var annotationUI;
  var rootThread;

  beforeEach(function () {
    var fakeUnicode = {
      normalize: function (s) { return s; },
      fold: function (s) { return s; },
    };

    angular.module('app', [])
      .service('annotationUI', require('../../annotation-ui'))
      .service('rootThread', require('../../root-thread'))
      .service('searchFilter', require('../../search-filter'))
      .service('viewFilter', require('../../view-filter'))
      .value('settings', {})
      .value('unicode', fakeUnicode);

    angular.mock.module('app');

    angular.mock.inject(function (_annotationUI_, _rootThread_) {
      annotationUI = _annotationUI_;
      rootThread = _rootThread_;
    });
  });

  it('should display newly loaded annotations', function () {
    annotationUI.addAnnotations(fixtures.annotations);
    assert.equal(rootThread.thread(annotationUI.getState()).children.length, 2);
  });

  it('should not display unloaded annotations', function () {
    annotationUI.addAnnotations(fixtures.annotations);
    annotationUI.removeAnnotations(fixtures.annotations);
    assert.equal(rootThread.thread(annotationUI.getState()).children.length, 0);
  });

  it('should filter annotations when a search is set', function () {
    annotationUI.addAnnotations(fixtures.annotations);
    annotationUI.setFilterQuery('second');
    assert.equal(rootThread.thread(annotationUI.getState()).children.length, 1);
    assert.equal(rootThread.thread(annotationUI.getState()).children[0].id, '2');
  });

  unroll('should sort annotations by #mode', function (testCase) {
    annotationUI.addAnnotations(fixtures.annotations);
    annotationUI.setSortKey(testCase.sortKey);
    var actualOrder = rootThread.thread(annotationUI.getState()).children.map(function (thread) {
      return thread.annotation.id;
    });
    assert.deepEqual(actualOrder, testCase.expectedOrder);
  }, [{
    sortKey: 'Oldest',
    expectedOrder: ['1','2'],
  },{
    sortKey: 'Newest',
    expectedOrder: ['2','1'],
  }]);
});
