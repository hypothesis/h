'use strict';

var createTask = require('./create-task');
var TaskQueue = require('../task-queue');

describe('TaskQueue', function () {
  it('executes each task in order', function () {
    var resolveOrder = [];
    var queue = new TaskQueue();

    var tasks = [createTask(0), createTask(1)];
    tasks.forEach(function (task) {
      task.done.then(function () { resolveOrder.push(task.id); });
    });

    queue.push(tasks[1].taskFn);
    queue.push(tasks[0].taskFn);

    return Promise.all([tasks[0].done, tasks[1].done]).then(function () {
      assert.deepEqual(resolveOrder, [1,0]);
    });
  });
});
