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

  // The public "group" is always available, regardless of what real groups (if
  // any) the user is a member of.
  var publicGroup = {
    name: 'Public',
    // We need a sentinel value to identify the public group (which is not
    // really a group). '__public__' won't clash with any of the hashids that
    // we use to identify real groups because the hashids never contain _.
    hashid: '__public__'
  };

  // Return the list of available groups.
  var groups = function() {
    return [publicGroup].concat(session.state.groups || []);
  };

  // Return the full object for the group with the given hashid.
  var getGroup = function(hashid) {
    for (var i = 0; i < groups().length; i++) {
      var group = groups()[i];
      if (group.hashid === hashid) {
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
    focusGroup: function(hashid) {
      var group_ = getGroup(hashid);
      if (group_ !== undefined) {
        focusedGroup = group_;
      };
    }
  };
}

module.exports = group;
