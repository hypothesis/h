'use strict';

// @ngInject
module.exports = function GroupListController(group) {
  var self = this;

  this.groups = function() {
    return group.groups();
  };

  this.focusedGroup = function() {
    return group.focusedGroup();
  };

  this.focusGroup = function(hashid) {
    return group.focusGroup(hashid);
  };
};
