import { createContext } from 'preact';

import type { FormFields } from '../forms-common/config';

export type FlashMessage = {
  type: 'success' | 'error';
  message: string;
};

export type ConfigBase = {
  csrfToken: string;
  flashMessages?: FlashMessage[];
  features: {
    log_in_with_facebook: boolean;
    log_in_with_google: boolean;
    log_in_with_orcid: boolean;
  };
  urls: {
    login: {
      facebook?: string;
      google?: string;
      orcid?: string;
    };
  };
};

/** Data passed to frontend for login form. */
export type LoginConfigObject = ConfigBase & {
  form: FormFields<{
    username: string;
    password: string;
  }>;
  forOAuth?: boolean;
};

/** Identity information if signing up with an identity provider such as Google. */
export type SocialLoginIdentity = {
  provider_unique_id: string;
};

/** Data passed to frontend for signup form. */
export type SignupConfigObject = ConfigBase & {
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
export type AccountSettingsConfigObject = ConfigBase & {
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
        url?: string;
      };
      facebook: {
        connected: boolean;
        provider_unique_id?: string;
        url?: string;
      };
      orcid: {
        connected: boolean;
        provider_unique_id?: string;
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
export type ProfileConfigObject = ConfigBase & {
  form: FormFields<{
    display_name: string;
    description: string;
    link: string;
    location: string;
    orcid: string;
  }>;
};

export type ConfigObject =
  | LoginConfigObject
  | SignupConfigObject
  | AccountSettingsConfigObject
  | ProfileConfigObject;

export const Config = createContext<ConfigObject | null>(null);
