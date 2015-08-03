/**
 * @ngdoc service
 * @name  groups
 *
 * @description
 * Get and set the UI's currently focused group.
 */
'use strict';

var STORAGE_KEY = 'hypothesis.groups.focus';

// @ngInject
function groups(localStorage, session) {
  // The currently focused group. This is the group that's shown as selected in
  // the groups dropdown, the annotations displayed are filtered to only ones
  // that belong to this group, and any new annotations that the user creates
  // will be created in this group.
  var focused;

  var all = function all() {
    return session.state.groups || [];
  };

  // Return the full object for the group with the given hashid.
  var get = function get(hashid) {
    var gs = all();
    for (var i = 0, max = gs.length; i < max; i++) {
      if (gs[i].hashid === hashid) {
        return gs[i];
      }
    }
  };

  return {
    all: all,
    get: get,

    // Return the currently focused group. If no group is explicitly focused we
    // will check localStorage to see if we have persisted a focused group from
    // a previous session. Lastly, we fall back to the first group available.
    focused: function() {
      if (focused) {
        return focused;
      }
      var fromStorage = get(localStorage.getItem(STORAGE_KEY));
      if (typeof fromStorage !== 'undefined') {
        focused = fromStorage;
        return focused;
      }
      return all()[0];
    },

    // Set the group with the passed hashid as the currently focused group.
    focus: function(hashid) {
      var g = get(hashid);
      if (typeof g !== 'undefined') {
        focused = g;
        localStorage.setItem(STORAGE_KEY, g.hashid);
      }
    }
  };
}

module.exports = groups;
