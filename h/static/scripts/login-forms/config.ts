import { createContext } from 'preact';

export type FlashMessage = {
  type: 'success' | 'error';
  message: string;
};

export type ConfigBase = {
  csrfToken: string;
  flashMessages?: FlashMessage[];
};

/** Data passed to frontend for login form. */
export type LoginConfigObject = ConfigBase & {
  formErrors?: {
    username?: string;
    password?: string;
  };
  formData?: {
    username?: string;
    password?: string;
  };
  forOAuth?: boolean;
  features: {
    log_in_with_orcid: boolean;
    log_in_with_google: boolean;
  };
};

/** Identity information if signing up with an identity provider such as Google. */
export type SocialLoginIdentity = {
  provider_unique_id: string;
};

/** Data passed to frontend for signup form. */
export type SignupConfigObject = ConfigBase & {
  formErrors?: {
    username?: string;
    password?: string;
    email?: string;
    privacy_accepted?: string;
  };
  formData?: {
    username: string;
    password: string;
    email: string;
    privacy_accepted: boolean;
    comms_opt_in: boolean;
  };
  identity?: SocialLoginIdentity;
};

export type ConfigObject = LoginConfigObject | SignupConfigObject;

export const Config = createContext<ConfigObject | null>(null);
