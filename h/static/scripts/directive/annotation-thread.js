'use strict';

function hiddenCount(thread) {
  var isHidden = thread.annotation && !thread.visible;
  return thread.children.reduce(function (count, reply) {
    return count + hiddenCount(reply);
  }, isHidden ? 1 : 0);
}

function showAllChildren(thread, showFn) {
  thread.children.forEach(function (child) {
    showFn({thread: child});
    showAllChildren(child, showFn);
  });
}

function showAllParents(thread, showFn) {
  while (thread.parent && thread.parent.annotation) {
    showFn({thread: thread.parent});
    thread = thread.parent;
  }
}

// @ngInject
function AnnotationThreadController() {
  this.toggleCollapsed = function () {
    this.onToggleReplies({id: this.thread.id});
  };

  /**
   * Show this thread and any of its children
   */
  this.showThreadAndReplies = function () {
    showAllParents(this.thread, this.onForceVisible);
    this.onForceVisible({thread: this.thread});
    showAllChildren(this.thread, this.onForceVisible);
  };

  /**
   * Return the total number of annotations in the current
   * thread which have been hidden because they do not match the current
   * search filter.
   */
  this.hiddenCount = function () {
    return hiddenCount(this.thread);
  };
}

/**
 * Renders a thread of annotations.
 */
module.exports = function () {
  return {
    restrict: 'E',
    bindToController: true,
    controllerAs: 'vm',
    controller: AnnotationThreadController,
    scope: {
      /** The annotation thread to render. */
      thread: '<',
      /**
       * Specify whether document information should be shown
       * on annotation cards.
       */
      showDocumentInfo: '<',
      /** Called when the user clicks on the expand/collapse replies toggle. */
      onToggleReplies: '&',
      /**
       * Called when the user clicks the button to show this thread or
       * one of its replies.
       */
      onForceVisible: '&',
    },
    template: require('../../../templates/client/annotation_thread.html'),
  };
};
