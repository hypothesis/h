/**
 * URL patterns for routes that the frontend router needs to match or
 * dynamically generate links for.
 *
 * These must be synchronized with h/routes.py.
 */
export const routes = {
  forgotPassword: '/forgot-password',
  login: '/login',
  loginWithORCID: '/oidc/login/orcid',
  loginWithGoogle: '/oidc/login/google',
  loginWithFacebook: '/oidc/login/facebook',
  signup: '/signup',
  signupWithEmail: '/signup/email',
  signupWithGoogle: '/signup/google',
  signupWithORCID: '/signup/orcid',
  signupWithFacebook: '/signup/facebook',
};
