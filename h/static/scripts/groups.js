/**
 * @ngdoc service
 * @name  groups
 *
 * @description
 * Get and set the UI's currently focused group.
 */
'use strict';

var baseURI = require('document-base-uri');

var STORAGE_KEY = 'hypothesis.groups.focus';

// @ngInject
function groups(localStorage, session, $rootScope, features, $http) {
  // The currently focused group. This is the group that's shown as selected in
  // the groups dropdown, the annotations displayed are filtered to only ones
  // that belong to this group, and any new annotations that the user creates
  // will be created in this group.
  var focused;

  var all = function all() {
    return session.state.groups || [];
  };

  // Return the full object for the group with the given id.
  var get = function get(id) {
    var gs = all();
    for (var i = 0, max = gs.length; i < max; i++) {
      if (gs[i].id === id) {
        return gs[i];
      }
    }
  };

  /** Leave the group with the given ID.
   * Returns a promise which resolves when the action completes.
   */
  function leave(id) {
    var response = $http({
      method: 'POST',
      url: baseURI + 'groups/' + id + '/leave',
    });

    // TODO - Optimistically call remove() to
    // remove the group locally when
    // https://github.com/hypothesis/h/pull/2587 has been merged

    return response;
  };

  return {
    all: all,
    get: get,

    leave: leave,

    // Return the currently focused group. If no group is explicitly focused we
    // will check localStorage to see if we have persisted a focused group from
    // a previous session. Lastly, we fall back to the first group available.
    focused: function() {
      if (focused) {
        return focused;
      } else if (features.flagEnabled('groups')) {
        var fromStorage = get(localStorage.getItem(STORAGE_KEY));
        if (typeof fromStorage !== 'undefined') {
          focused = fromStorage;
          return focused;
        }
      }
      return all()[0];
    },

    // Set the group with the passed id as the currently focused group.
    focus: function(id) {
      var g = get(id);
      if (typeof g !== 'undefined') {
        focused = g;
        localStorage.setItem(STORAGE_KEY, g.id);
        $rootScope.$broadcast('groupFocused', g.id);
      }
    }
  };
}

module.exports = groups;
