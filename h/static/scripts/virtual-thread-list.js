'use strict';

var EventEmitter = require('tiny-emitter');
var debounce = require('lodash.debounce');
var inherits = require('inherits');

/**
 * VirtualThreadList is a helper for virtualizing the annotation thread list.
 *
 * 'Virtualizing' the thread list hugely optimizes updates for the UI by only
 * creating annotation cards for annotations which are either in or near the
 * viewport.
 *
 * This technique is used in all native UI frameworks but is especially
 * important as long as Angular is used for the view layer of the application
 * because every active watcher/template expression contributes overhead to the
 * $digest cycle and thus towards a feeling of lagginess in the UI.
 *
 * @param {Window} container - The Window displaying the list of annotation threads.
 * @param {Thread} rootThread - The initial Thread object for the top-level
 *        threads.
 */
function VirtualThreadList($scope, window_, rootThread) {
  var self = this;

  this._rootThread = rootThread;

  // Cache of thread ID -> last-seen height
  this._heights = {};

  this.window = window_;

  var debouncedUpdate = debounce(function () {
    self._updateVisibleThreads();
    $scope.$digest();
  }, 20);
  this.window.addEventListener('scroll', debouncedUpdate);
  this.window.addEventListener('resize', debouncedUpdate);

  this._detach = function () {
    this.window.removeEventListener('scroll', debouncedUpdate);
    this.window.removeEventListener('resize', debouncedUpdate);
  };
}
inherits(VirtualThreadList, EventEmitter);

/**
 * Detach event listeners and clear any pending timeouts.
 *
 * This should be invoked when the UI view presenting the virtual thread list
 * is torn down.
 */
VirtualThreadList.prototype.detach = function () {
  this._detach();
};

/**
 * Sets the root thread containing all conversations matching the current
 * filters.
 *
 * This should be called with the current Thread object whenever the set of
 * matching annotations changes.
 */
VirtualThreadList.prototype.setRootThread = function (thread) {
  this._rootThread = thread;
  this._updateVisibleThreads();
};

/**
 * Sets the actual height for a thread.
 *
 * When calculating the amount of space required for offscreen threads,
 * the actual or 'last-seen' height is used if known. Otherwise an estimate
 * is used.
 */
VirtualThreadList.prototype.setThreadHeight = function (id, height) {
  if (this._heights[id] === height) {
    return;
  }
  this._heights[id] = height;
};

/**
 * Recalculates the set of visible threads and estimates of the amount of space
 * required for offscreen threads above and below the viewport.
 *
 * Emits a `changed` event with the recalculated set of visible threads.
 */
VirtualThreadList.prototype._updateVisibleThreads = function () {
  // Space above the viewport in pixels which should be considered 'on-screen'
  // when calculating the set of visible threads
  var MARGIN_ABOVE = 800;
  // Same as MARGIN_ABOVE but for the space below the viewport
  var MARGIN_BELOW = 800;
  // Default guess of the height required for a threads that have not been
  // measured
  var DEFAULT_HEIGHT = 200;

  var offscreenLowerHeight = 0;
  var offscreenUpperHeight = 0;
  var visibleThreads = [];

  var allThreads = this._rootThread.children;
  var visibleHeight = this.window.innerHeight;
  var usedHeight = 0;
  var thread;

  for (var i = 0; i < allThreads.length; i++) {
    thread = allThreads[i];
    var threadHeight = this._heights[thread.id] || DEFAULT_HEIGHT;

    if (usedHeight + threadHeight < this.window.pageYOffset - MARGIN_ABOVE) {
      // Thread is above viewport
      offscreenUpperHeight += threadHeight;
    } else if (usedHeight <
      this.window.pageYOffset + visibleHeight + MARGIN_BELOW) {
      // Thread is either in or close to the viewport
      visibleThreads.push(allThreads[i]);
    } else {
      // Thread is below viewport
      offscreenLowerHeight += threadHeight;
    }

    usedHeight += threadHeight;
  }

  this.emit('changed', {
    offscreenLowerHeight: offscreenLowerHeight,
    offscreenUpperHeight: offscreenUpperHeight,
    visibleThreads: visibleThreads,
  });
};

module.exports = VirtualThreadList;
