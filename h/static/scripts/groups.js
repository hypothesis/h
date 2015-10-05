/**
 * @ngdoc service
 * @name  groups
 *
 * @description Provides access to the list of groups that the user is currently
 *              a member of and the currently selected group in the UI.
 *
 *              The list of groups is initialized from the session state
 *              and can then later be updated using the add() and remove()
 *              methods.
 */
'use strict';

var STORAGE_KEY = 'hypothesis.groups.focus';

// @ngInject
function groups(localStorage, session, $rootScope, features) {
  // The currently focused group. This is the group that's shown as selected in
  // the groups dropdown, the annotations displayed are filtered to only ones
  // that belong to this group, and any new annotations that the user creates
  // will be created in this group.
  var focused;

  function all() {
    return session.state.groups || [];
  };

  // Return the full object for the group with the given id.
  function get(id) {
    var gs = all();
    for (var i = 0, max = gs.length; i < max; i++) {
      if (gs[i].id === id) {
        return gs[i];
      }
    }
  };

  /** Update the groups list by adding a group that the user has joined. */
  function add(group) {
    var otherGroups = all().filter(function (existingGroup) {
      return existingGroup.id !== group.id;
    });
    session.state.groups = otherGroups.concat(group);
    $rootScope.$broadcast('groupJoined', group.id);
  }

  /** Update the groups list by removing a group that the user has left. */
  function remove(group) {
    var otherGroups = all().filter(function (existingGroup) {
      return existingGroup.id !== group.id;
    });
    session.state.groups = otherGroups;

    if (focused.id === group.id) {
      focused = null;
    }

    $rootScope.$broadcast('groupLeft', group.id);
  }

  /** Return the currently focused group. If no group is explicitly focused we
   * will check localStorage to see if we have persisted a focused group from
   * a previous session. Lastly, we fall back to the first group available.
   */
  function focused() {
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
  }

  /** Set the group with the passed id as the currently focused group. */
  function focus(id) {
   var g = get(id);
   if (typeof g !== 'undefined') {
     focused = g;
     localStorage.setItem(STORAGE_KEY, g.id);
     $rootScope.$broadcast('groupFocused', g.id);
   }
  }

  return {
    all: all,
    get: get,

    add: add,
    remove: remove,

    focused: focused,
    focus: focus,
  };
}

module.exports = groups;
