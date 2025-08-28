/**
 * URL patterns for routes that the frontend router needs to match or
 * dynamically generate links for.
 *
 * These must be synchronized with h/routes.py.
 */
export const routes = {
  accountDelete: '/account/delete',
  accountDeveloper: '/account/developer',
  accountNotifications: '/account/settings/notifications',
  accountSettings: '/account/settings',
  forgotPassword: '/forgot-password',
  groups: {
    new: '/groups/new',
    edit: '/groups/:pubid/edit',
    editMembers: '/groups/:pubid/edit/members',
    moderation: '/groups/:pubid/moderate',
  },
  login: '/login',
  profile: '/account/profile',
  signup: '/signup',
  signupWithEmail: '/signup/email',
  signupWithFacebook: '/signup/facebook',
  signupWithGoogle: '/signup/google',
  signupWithORCID: '/signup/orcid',
};
