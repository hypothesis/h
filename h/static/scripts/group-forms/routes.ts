/**
 * URL patterns for routes that the frontend router needs to match or
 * dynamically generate links for.
 *
 * These must be synchronized with h/routes.py.
 */
export const routes = {
  api: {
    group: {
      members: '/api/groups/:pubid/members',
    },
  },
  groups: {
    new: '/groups/new',
    edit: '/groups/:pubid/edit',
    editMembers: '/groups/:pubid/edit/members',
  },
};
