'use strict';

/**
 * A helper for creating fake async tasks in tests.
 *
 * The returned object has a `taskFn` to run the task and a `done` Promise
 * that resolves when the task is executed.
 */
function createTask(id) {
  var resolve;
  var done = new Promise(function (resolve_) {
    resolve = resolve_;
  });
  var taskFn = function () {
    resolve();
    return done;
  };
  return {id: id, taskFn: taskFn, done: done};
}

module.exports = createTask;
