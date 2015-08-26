/**
 * @ngdoc service
 * @name  group
 *
 * @description
 * Get and set the UI's currently focused group.
 */
'use strict';

// @ngInject
function group(session) {
  // The currently focused group. This is the group that's shown as selected in
  // the groups dropdown, the annotations displayed are filtered to only ones
  // that belong to this group, and any new annotations that the user creates
  // will be created in this group.
  var focusedGroup;

  // Return the list of available groups.
  var groups = function() {
    return session.state.groups || [];
  };

  // Return the full object for the group with the given id.
  var getGroup = function(id) {
    for (var i = 0; i < groups().length; i++) {
      var group = groups()[i];
      if (group.id === id) {
        return group;
      }
    }
  };

  return {
    groups: groups,
    getGroup: getGroup,

    // Return the currently focused group.
    focusedGroup: function() {
      return focusedGroup || groups()[0];
    },

    // Set the named group as the currently focused group.
    focusGroup: function(id) {
      var group_ = getGroup(id);
      if (group_ !== undefined) {
        focusedGroup = group_;
      }
    }
  };
}

module.exports = group;
