// This module contains types for the configuration passed from the backend
// to the frontend in the page HTML as a JSON object.
import { createContext } from 'preact';

import type { GroupType } from './util/api';
import type { FormFields } from './util/config';

export type APIConfig = {
  method: string;
  url: string;
  headers: Record<PropertyKey, unknown>;
};

export type Group = {
  pubid: string;
  name: string;
  description: string;
  link: string;
  type: GroupType;
  num_annotations: number;
  pre_moderated: boolean;
};

/** Common configuration for group management forms. */
export type GroupFormsConfigObject = {
  api: {
    createGroup: APIConfig;
    updateGroup?: APIConfig;
    readGroupMembers?: APIConfig;
    editGroupMember?: APIConfig;
    removeGroupMember?: APIConfig;
    groupAnnotations?: APIConfig;
    annotationModeration?: APIConfig;
    annotationDetail?: APIConfig;
  };
  context: {
    group: Group | null;
    user: {
      userid: string;
    };
  };
  features: {
    group_members: boolean;
    group_type: boolean;
    group_moderation: boolean;
    pre_moderation: boolean;
  };
  routes: {
    'activity.user_search': string;
  };
};

export const GroupFormsConfig = createContext<GroupFormsConfigObject | null>(
  null,
);

export type FlashMessage = {
  type: 'success' | 'error';
  message: string;
};

/** Common configuration for login/signup forms. */
export type LoginFormsConfigBase = {
  csrfToken: string;
  flashMessages?: FlashMessage[];
  features: {
    log_in_with_facebook: boolean;
    log_in_with_google: boolean;
    log_in_with_orcid: boolean;
  };

  // URLs for social login. These are present on the login and initial signup
  // page but missing on the `/signup/{provider}` page.
  urls?: {
    signup?: string;
    login?: {
      username_or_email?: string;
      facebook?: string;
      google?: string;
      orcid?: string;
    };
  };
};

/** Data passed to frontend for login form. */
export type LoginConfigObject = LoginFormsConfigBase & {
  form: FormFields<{
    username: string;
    password: string;
  }>;
  forOAuth?: boolean;
};

/** Identity information if signing up with an identity provider such as Google. */
export type SocialLoginIdentity = {
  provider_unique_id: string;
  email?: string;
};

/** Data passed to frontend for signup form. */
export type SignupConfigObject = LoginFormsConfigBase & {
  forOAuth?: boolean;
  form: FormFields<{
    username: string;
    password: string;
    email: string;
    privacy_accepted: boolean;
    comms_opt_in: boolean;
  }>;
  identity?: SocialLoginIdentity;
};

/** Configuration for the 'Account settings' forms. */
export type AccountSettingsConfigObject = LoginFormsConfigBase & {
  forms: {
    email: FormFields<{
      email: string;
      password: string;
    }>;
    password: FormFields<{
      password: string;
      new_password: string;
      new_password_confirm: string;
    }>;
  };
  context: {
    user: { email: string; has_password: boolean };
    identities?: {
      google: {
        connected: boolean;
        provider_unique_id?: string;
        email?: string;
        url?: string;
      };
      facebook: {
        connected: boolean;
        provider_unique_id?: string;
        email?: string;
        url?: string;
      };
      orcid: {
        connected: boolean;
        provider_unique_id?: string;
        email?: string;
        url?: string;
      };
    };
  };
  routes: {
    'oidc.connect.google'?: string;
    'oidc.connect.facebook'?: string;
    'oidc.connect.orcid'?: string;
    identity_delete: string;
  };
};

/** Configuration for Edit Profile form. */
export type ProfileConfigObject = LoginFormsConfigBase & {
  form: FormFields<{
    display_name: string;
    description: string;
    link: string;
    location: string;
    orcid: string;
  }>;
};

export type DeveloperConfigObject = LoginFormsConfigBase & {
  token?: string;
};

export type LoginFormsConfigObject =
  | LoginConfigObject
  | SignupConfigObject
  | AccountSettingsConfigObject
  | ProfileConfigObject
  | DeveloperConfigObject;

export const LoginFormsConfig = createContext<LoginFormsConfigObject | null>(
  null,
);
