'use strict';

angular.module('h').controller(
  'GroupListCtrl', ['group', function(group) {
        var self = this;

        self.groups = function() {
          return group.groups();
        };

        self.focusedGroup = function() {
          return group.focusedGroup();
        };

        self.focusGroup = function(hashid) {
          return group.focusGroup(hashid);
        };
      }
    ]
  );
