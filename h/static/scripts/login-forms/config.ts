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
  form: FormFields<{
    username: string;
    password: string;
    email: string;
    privacy_accepted: boolean;
    comms_opt_in: boolean;
  }>;
  identity?: SocialLoginIdentity;
};

export type ConfigObject = LoginConfigObject | SignupConfigObject;

export const Config = createContext<ConfigObject | null>(null);
