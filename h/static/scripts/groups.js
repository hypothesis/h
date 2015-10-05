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

var baseURI = require('document-base-uri');

var STORAGE_KEY = 'hypothesis.groups.focus';

var events = require('./events');

// @ngInject
function groups(localStorage, session, $rootScope, features, $http) {
  // The currently focused group. This is the group that's shown as selected in
  // the groups dropdown, the annotations displayed are filtered to only ones
  // that belong to this group, and any new annotations that the user creates
  // will be created in this group.
  var focusedGroup;

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


  /** Return the currently focused group. If no group is explicitly focused we
   * will check localStorage to see if we have persisted a focused group from
   * a previous session. Lastly, we fall back to the first group available.
   */
  function focused() {
    if (focusedGroup) {
     return focusedGroup;
    } else if (features.flagEnabled('groups')) {
     var fromStorage = get(localStorage.getItem(STORAGE_KEY));
     if (fromStorage) {
       var matches = all().filter(function (group) {
         return group.id === fromStorage.id;
       });
       if (matches.length > 0) {
         focusedGroup = matches[0];
       }
       return focusedGroup;
     }
    }
    return all()[0];
  }

  /** Set the group with the passed id as the currently focused group. */
  function focus(id) {
   var g = get(id);
   if (typeof g !== 'undefined') {
     focusedGroup = g;
     localStorage.setItem(STORAGE_KEY, g.id);
     $rootScope.$broadcast(events.GROUP_FOCUSED, g.id);
   }
  }

  // reset the focused group if the user leaves it
  $rootScope.$on(events.SESSION_CHANGED, function () {
    if (focusedGroup) {
      var match = session.state.groups.filter(function (group) {
        return group.id === focusedGroup.id;
      });
      if (match.length === 0) {
        focusedGroup = null;
        $rootScope.$broadcast(events.GROUP_FOCUSED, focused());
      }
    }
  });

  return {
    all: all,
    get: get,

    leave: leave,

    focused: focused,
    focus: focus,
  };
}

module.exports = groups;
