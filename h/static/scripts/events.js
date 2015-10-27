/**
 * This module defines the set of global events that are dispatched
 * on $rootScope
 */
module.exports = {
  /** Broadcast when the currently selected group changes */
  GROUP_FOCUSED: 'groupFocused',
  /** Broadcast when the list of groups changes */
  GROUPS_CHANGED: 'groupsChanged',
  /** Broadcast when the signed-in user changes */
  USER_CHANGED: 'userChanged',
  /** Broadcast when the session state is updated.
   * This event is NOT broadcast after the initial session load.
   */
  SESSION_CHANGED: 'sessionChanged',
};
