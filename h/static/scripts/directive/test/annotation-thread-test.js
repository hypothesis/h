'use strict';

var angular = require('angular');

var annotationThread = require('../annotation-thread');
var util = require('./util');

function PageObject(element) {
  this.annotations = function () {
    return Array.from(element[0].querySelectorAll('annotation'));
  };
  this.replies = function () {
    return Array.from(element[0].querySelectorAll('annotation-thread'));
  };
  this.replyList = function () {
    return element[0].querySelector('.thread-replies');
  };
  this.isHidden = function (element) {
    return element.classList.contains('ng-hide');
  };
}

describe('annotationThread', function () {
  before(function () {
    angular.module('app', [])
      .directive('annotationThread', annotationThread);
  });

  beforeEach(function () {
    angular.mock.module('app');
  });

  it('renders the tree structure of parent and child annotations', function () {
    var element = util.createDirective(document, 'annotationThread', {
      thread: {
        id: '1',
        annotation: {id: '1', text: 'text'},
        children: [{
          id: '2',
          annotation: {id: '2', text: 'areply'},
          children: [],
        }],
        visible: true,
      },
    });
    var pageObject = new PageObject(element);
    assert.equal(pageObject.annotations().length, 2);
    assert.equal(pageObject.replies().length, 1);
  });

  it('does not render hidden threads', function () {
    var element = util.createDirective(document, 'annotationThread', {
      thread: {
        id: '1',
        annotation: {id: '1'},
        visible: false,
        children: []
      }
    });
    var pageObject = new PageObject(element);
    assert.equal(pageObject.annotations().length, 1);
    assert.isTrue(pageObject.isHidden(pageObject.annotations()[0]));
  });

  it('shows replies if not collapsed', function () {
    var element = util.createDirective(document, 'annotationThread', {
      thread: {
        id: '1',
        annotation: {id: '1'},
        visible: true,
        children: [{
          id: '2',
          annotation: {id: '2'},
          children: [],
          visible: true,
        }],
        collapsed: false,
      }
    });
    var pageObject = new PageObject(element);
    assert.equal(pageObject.replies().length, 1);
  });

  it('does not show replies if collapsed', function () {
    var element = util.createDirective(document, 'annotationThread', {
      thread: {
        id: '1',
        annotation: {id: '1'},
        visible: true,
        children: [{
          id: '2',
          annotation: {id: '2'},
          children: [],
          visible: true,
        }],
        collapsed: true,
      }
    });
    var pageObject = new PageObject(element);
    assert.isTrue(pageObject.isHidden(pageObject.replyList()));
  });

  describe('#toggleCollapsed', function () {
    it('toggles replies', function () {
      var onToggleReplies = sinon.stub();
      var element = util.createDirective(document, 'annotationThread', {
        thread: {
          id: '123',
          annotation: {id: '123'},
          children: [],
        },
        onToggleReplies: {
          args: ['id'],
          callback: onToggleReplies,
        }
      });
      element.ctrl.toggleCollapsed();
      assert.calledWith(onToggleReplies, '123');
    });
  });

  describe('#showThreadAndReplies', function () {
    it('reveals all parents and replies', function () {
      var onForceVisible = sinon.stub();
      var thread = {
        id: '123',
        annotation: {id: '123'},
        children: [{
          id: 'child-id',
          annotation: {id: 'child-id'},
          children: [],
        }],
        parent: {
          id: 'parent-id',
          annotation: {id: 'parent-id'},
        },
      };
      var element = util.createDirective(document, 'annotationThread', {
        thread: thread,
        onForceVisible: {
          args: ['thread'],
          callback: onForceVisible,
        },
      });
      element.ctrl.showThreadAndReplies();
      assert.calledWith(onForceVisible, thread.parent);
      assert.calledWith(onForceVisible, thread);
      assert.calledWith(onForceVisible, thread.children[0]);
    });
  });
});
