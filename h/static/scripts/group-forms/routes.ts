/**
 * URL patterns for routes that the frontend router needs to match or
 * dynamically generate links for.
 *
 * These must be synchronized with h/routes.py.
 */
export const routes = {
  groups: {
    new: '/groups/new',
    edit: '/groups/:pubid/edit',
    editMembers: '/groups/:pubid/edit/members',
    moderation: '/groups/:pubid/moderate',
  },
};
