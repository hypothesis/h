'use strict';

var angular = require('angular');

var annotationUIFactory = require('../annotation-ui');

describe('AnnotationUISync', function () {
  var sandbox = sinon.sandbox.create();
  var $digest;
  var publish;
  var fakeBridge;
  var annotationUI;
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

    annotationUI = annotationUIFactory({});
    annotationUI.addAnnotations([
      {id: 'id1', $$tag: 'tag1'},
      {id: 'id2', $$tag: 'tag2'},
      {id: 'id3', $$tag: 'tag3'},
    ]);
    createAnnotationUISync = function () {
      new AnnotationUISync(
        $rootScope, fakeWindow, annotationUI, fakeBridge
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
    it('selects annotations which have an ID', function () {
      createAnnotationUISync();
      annotationUI.selectAnnotations = sinon.stub();
      publish('showAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.calledWith(annotationUI.selectAnnotations, ['id1', 'id2', 'id3']);
    });

    it('does not select annotations which do not have an ID', function () {
      createAnnotationUISync();
      annotationUI.selectAnnotations = sinon.stub();
      publish('showAnnotations', ['tag1', 'tag-for-a-new-annotation']);
      assert.calledWith(annotationUI.selectAnnotations, ['id1']);
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('showAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "focusAnnotations" event', function () {
    it('focuses the annotations', function () {
      createAnnotationUISync();
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.deepEqual(annotationUI.getState().focusedAnnotationMap, {
        tag1: true,
        tag2: true,
        tag3: true,
      });
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "toggleAnnotationSelection" event', function () {
    it('toggles the selected state of the annotations', function () {
      createAnnotationUISync();
      annotationUI.toggleSelectedAnnotations = sinon.stub();
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3']);
      assert.calledWith(annotationUI.toggleSelectedAnnotations, ['id1', 'id2', 'id3']);
    });

    it('triggers a digest', function () {
      createAnnotationUISync();
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3']);
      assert.called($digest);
    });
  });

  describe('on "setVisibleHighlights" event', function () {
    it('updates the annotationUI state', function () {
      createAnnotationUISync();
      publish('setVisibleHighlights', true);
      assert.equal(annotationUI.getState().visibleHighlights, true);
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
