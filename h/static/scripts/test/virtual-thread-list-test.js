'use strict';

var proxyquire = require('proxyquire');

var VirtualThreadList = proxyquire('../virtual-thread-list', {
  'lodash.debounce': function (fn) {
    // Make debounced functions execute immediately
    return fn;
  },
});
var util = require('./util');
var unroll = util.unroll;

describe('VirtualThreadList', function () {
  var lastState;
  var threadList;

  var fakeScope;
  var fakeWindow;

  function idRange(start, end) {
    var ary = [];
    for (var i=start; i <= end; i++) {
      ary.push('t' + i.toString());
    }
    return ary;
  }

  function threadIDs(threads) {
    return threads.map(function (thread) { return thread.id; });
  }

  function generateRootThread(count) {
    return {
      annotation: undefined,
      children: idRange(0, count-1).map(function (id) {
        return {id: id, annotation: undefined, children: []};
      }),
    };
  }

  beforeEach(function () {
    fakeScope = {$digest: sinon.stub()};

    fakeWindow = {
      listeners: {},
      addEventListener: function (event, listener) {
        this.listeners[event] = this.listeners[event] || [];
        this.listeners[event].push(listener);
      },
      removeEventListener: function (event, listener) {
        this.listeners[event] = this.listeners[event].filter(function (fn) {
          return fn !== listener;
        });
      },
      trigger: function (event) {
        this.listeners[event].forEach(function (cb) {
          cb();
        });
      },
      innerHeight: 100,
      pageYOffset: 0,
    };

    var rootThread = {annotation: undefined, children: []};
    threadList = new VirtualThreadList(fakeScope, fakeWindow, rootThread);
    threadList.on('changed', function (state) {
      lastState = state;
    });
  });

  unroll('generates expected state when #when', function (testCase) {
    var thread = generateRootThread(testCase.threads);

    fakeWindow.pageYOffset = testCase.scrollOffset;
    fakeWindow.innerHeight = testCase.windowHeight;

    threadList.setRootThread(thread);

    var visibleIDs = threadIDs(lastState.visibleThreads);
    assert.deepEqual(visibleIDs, testCase.expectedVisibleThreads);
    assert.equal(lastState.offscreenUpperHeight, testCase.expectedHeightAbove);
    assert.equal(lastState.offscreenLowerHeight, testCase.expectedHeightBelow);
  },[{
    when: 'window is scrolled to top of list',
    threads: 100,
    scrollOffset: 0,
    windowHeight: 300,
    expectedVisibleThreads: idRange(0, 5),
    expectedHeightAbove: 0,
    expectedHeightBelow: 18800,
  },{
    when: 'window is scrolled to middle of list',
    threads: 100,
    scrollOffset: 2000,
    windowHeight: 300,
    expectedVisibleThreads: idRange(5, 15),
    expectedHeightAbove: 1000,
    expectedHeightBelow: 16800,
  },{
    when: 'window is scrolled to bottom of list',
    threads: 100,
    scrollOffset: 18800,
    windowHeight: 300,
    expectedVisibleThreads: idRange(89, 99),
    expectedHeightAbove: 17800,
    expectedHeightBelow: 0,
  }]);

  unroll('recalculates when a window.#event occurs', function (testCase) {
    lastState = null;
    fakeWindow.trigger(testCase.event);
    assert.ok(lastState);
  },[{
    event: 'resize',
  },{
    event: 'scroll',
  }]);

  it('recalculates when root thread changes', function () {
    threadList.setRootThread({annotation: undefined, children: []});
    assert.ok(lastState);
  });

  describe('#setThreadHeight', function () {
    unroll('affects visible threads', function (testCase) {
      var thread = generateRootThread(10);
      fakeWindow.innerHeight = 500;
      fakeWindow.pageYOffset = 0;
      idRange(0,10).forEach(function (id) {
        threadList.setThreadHeight(id, testCase.threadHeight);
      });
      threadList.setRootThread(thread);
      assert.deepEqual(threadIDs(lastState.visibleThreads),
        testCase.expectedVisibleThreads);
    },[{
      threadHeight: 1000,
      expectedVisibleThreads: idRange(0,1),
    },{
      threadHeight: 300,
      expectedVisibleThreads: idRange(0,4),
    }]);
  });

  describe('#detach', function () {
    unroll('stops listening to window.#event events', function (testCase) {
      threadList.detach();
      lastState = null;
      fakeWindow.trigger(testCase.event);
      assert.isNull(lastState);
    },[{
      event: 'resize',
    },{
      event: 'scroll',
    }]);
  });
});
