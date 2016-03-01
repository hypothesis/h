'use strict';

function hiddenReplyCount(thread) {
  return thread.children.reduce(function (count, reply) {
    return count + (reply.visible ? 0 : 1) + hiddenReplyCount(reply);
  }, 0);
}

function showAllChildren(thread, showFn) {
  thread.children.forEach(function (child) {
    showFn({id: child.annotation.id});
    showAllChildren(child, showFn);
  });
}

// @ngInject
function AnnotationThreadController() {
  this.toggleCollapsed = function () {
    this.onToggleReplies({id: this.thread.annotation.id});
  };

  /**
   * Show this thread and any of its children
   */
  this.showThreadAndReplies = function () {
    this.onForceVisible({id: this.thread.annotation.id});
    showAllChildren(this.thread, this.onForceVisible);
  };

  /**
   * Return the total number of annotations in the current
   * thread which have been hidden because they do not match the current
   * search filter.
   */
  this.hiddenReplyCount = function () {
    var count = this.thread.visible ? 0 : 1;
    return count + hiddenReplyCount(this.thread);
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
