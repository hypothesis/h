'use strict';

/**
 * A queue which executes a series of Promise-yielding tasks sequentially.
 *
 * Call push() to enqueue a new task. All tasks are executed in serial.
 *
 * If we end up with more sophisticated needs, we might want to look at
 * a package such as bottleneck.
 */
function TaskQueue() {
  this._queue = [];
  this._activeTask = null;
}

TaskQueue.prototype._runNext = function () {
  var self = this;
  if (this._activeTask || !this._queue.length) {
    return;
  }
  var fn = this._queue.shift();
  this._activeTask = fn();
  this._activeTask.then(function () {
    self._activeTask = null;
    self._runNext();
  }).catch(function () {
    self._activeTask = null;
    self._runNext();
  });
};

/**
 * Schedule a task.
 *
 * @param {Function} fn - A function that when executed, returns a Promise
 *        for completion of the task.
 */
TaskQueue.prototype.push = function (fn) {
  this._queue.push(fn);
  this._runNext();
};

module.exports = TaskQueue;
