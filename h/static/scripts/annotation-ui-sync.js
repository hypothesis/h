'use strict';

var uiConstants = require('./ui-constants');

/**
 * Uses a channel between the sidebar and the attached frames to ensure
 * the interface remains in sync.
 *
 * @name AnnotationUISync
 * @param {$window} $window An Angular window service.
 * @param {Bridge} bridge
 * @param {AnnotationUI} annotationUI An instance of the AnnotatonUI service
 * @description
 * Listens for incoming events over the bridge concerning the annotation
 * interface and updates the applications internal state. It also ensures
 * that the messages are broadcast out to other frames.
 */
// @ngInject
function AnnotationUISync($rootScope, $window, annotationUI, bridge) {
  function lookupByTag(tag) {
    return annotationUI.getState().annotations.find(function (annot) {
      return annot.$$tag === tag;
    });
  }

  function findIDsForTags(tags) {
    var ids = [];
    tags.forEach(function (tag) {
      var annot = lookupByTag(tag);
      if (annot && annot.id) {
        ids.push(annot.id);
      }
    });
    return ids;
  }

  var channelListeners = {
    showAnnotations: function (tags) {
      var ids = findIDsForTags(tags || []);
      annotationUI.selectAnnotations(ids);
      annotationUI.selectTab(uiConstants.TAB_ANNOTATIONS);
    },
    focusAnnotations: function (tags) {
      annotationUI.focusAnnotations(tags || []);
    },
    toggleAnnotationSelection: function (tags) {
      var ids = findIDsForTags(tags || []);
      annotationUI.toggleSelectedAnnotations(ids);
    },
    setVisibleHighlights: function (state) {
      if (typeof state !== 'boolean') {
        state = true;
      }
      if (annotationUI.getState().visibleHighlights !== state) {
        annotationUI.setShowHighlights(state);
        bridge.call('setVisibleHighlights', state);
      }
    }
  };

  // Because the channel events are all outside of the angular framework we
  // need to inform Angular that it needs to re-check it's state and re-draw
  // any UI that may have been affected by the handlers.
  var ensureDigest = function (fn) {
    return function () {
      fn.apply(this, arguments);
      $rootScope.$digest();
    };
  };

  for (var channel in channelListeners) {
    if (Object.prototype.hasOwnProperty.call(channelListeners, channel)) {
      var listener = channelListeners[channel];
      bridge.on(channel, ensureDigest(listener));
    }
  }

  var onConnect = function (channel, source) {
    if (source === $window.parent) {
      // The host initializes its own state
      return;
    } else {
      // Synchronize the state of guests
      channel.call('setVisibleHighlights', annotationUI.getState().visibleHighlights);
    }
  };

  bridge.onConnect(onConnect);
}

module.exports = AnnotationUISync;
