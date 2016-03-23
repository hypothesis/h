'use strict';

var angular = require('angular');

describe('AnnotationUISync', function () {
  var sandbox = sinon.sandbox.create();
  var $digest;
  var publish;
  var fakeBridge;
  var fakeAnnotationUI;
  var fakeAnnotationSync;
  var createAnnotationUISync;
  var createChannel = function () {
    return { call: sandbox.stub() };
  };
  var PARENT_WINDOW = 'PARENT_WINDOW';

  before(function () {
    angular.module('h', [])
      .value('AnnotationUISync', require('../annotation-ui-sync'));
  });

  beforeEach(angular.mock.module('h'));
  beforeEach(angular.mock.inject(function (AnnotationUISync, $rootScope) {
    $digest = sandbox.stub($rootScope, '$digest');
    var listeners = {};
    publish = function (method) {
      var args = [].slice.apply(arguments);
      return listeners[method].apply(null, args.slice(1));
    };

    var fakeWindow = { parent: PARENT_WINDOW };
    fakeBridge = {
      on: sandbox.spy(function (method, fn) { listeners[method] = fn; }),
      call: sandbox.stub(),
      onConnect: sandbox.stub(),
      links: [
        { window: PARENT_WINDOW, channel: createChannel() },
        { window: 'ANOTHER_WINDOW', channel: createChannel() },
        { window: 'THIRD_WINDOW', channel: createChannel() }
      ]
    };

    fakeAnnotationSync = {
      getAnnotationForTag: function (tag) {
        return { id: Number(tag.replace('tag', '')) };
      }
    };

    fakeAnnotationUI = {
      focusAnnotations: sandbox.stub(),
      selectAnnotations: sandbox.stub(),
      xorSelectedAnnotations: sandbox.stub(),
      visibleHighlights: false,
    };

    createAnnotationUISync = function () {
      new AnnotationUISync(
        $rootScope, fakeWindow, fakeBridge, fakeAnnotationSync,
        fakeAnnotationUI
      );
    };
  }));

  afterEach(function () {
    sandbox.restore();
  });

  describe('on bridge connection', function () {
    describe('when the source is not the parent window', function () {
      it('broadcasts the visibility settings to the channel', function () {
        var channel = createChannel();
        fakeBridge.onConnect.callsArgWith(0, channel, {});

        createAnnotationUISync();

        assert.calledWith(channel.call, 'setVisibleHighlights', false);
      });
    });

    describe('when the source is the parent window', function () {
      it('does nothing', function () {
        var channel = { call: sandbox.stub() };
        fakeBridge.onConnect.callsArgWith(0, channel, PARENT_WINDOW);

        createAnnotationUISync();
        assert.notCalled(channel.call);
      });
    });
  });

  describe('on "showAnnotations" event', function () {
    it('updates the annotationUI to include the shown annotations', function () {
      createAnnotationUISync();
      publish('showAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called(fakeAnnotationUI.selectAnnotations);
      assert.calledWith(fakeAnnotationUI.selectAnnotations, [
        { id: 1 }, { id: 2 }, { id: 3 }
      ]);
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('showAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "focusAnnotations" event', function () {
    it('updates the annotationUI to show the provided annotations', function () {
      createAnnotationUISync();
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called(fakeAnnotationUI.focusAnnotations);
      assert.calledWith(fakeAnnotationUI.focusAnnotations, [
        { id: 1 }, { id: 2 }, { id: 3 }
      ]);
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "toggleAnnotationSelection" event', function () {
    it('updates the annotationUI to show the provided annotations', function () {
      createAnnotationUISync();
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3']);
      assert.called(fakeAnnotationUI.xorSelectedAnnotations);
      assert.calledWith(fakeAnnotationUI.xorSelectedAnnotations, [
        { id: 1 }, { id: 2 }, { id: 3 }
      ]);
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "setVisibleHighlights" event', function () {
    it('updates the annotationUI with the new value', function () {
      createAnnotationUISync();
      publish('setVisibleHighlights', true);
      assert.equal(fakeAnnotationUI.visibleHighlights, true);
    });

    it('notifies the other frames of the change', function () {
      createAnnotationUISync();
      publish('setVisibleHighlights', true);
      assert.calledWith(fakeBridge.call, 'setVisibleHighlights', true);
    });

    it('triggers a digest of the application state', function () {
      createAnnotationUISync();
      publish('setVisibleHighlights', true);
      assert.called($digest);
    });
  });
});
