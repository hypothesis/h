import { createContext } from 'preact';

export type ConfigBase = {
  csrfToken: string;
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
  };
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
};

export type ConfigObject = LoginConfigObject | SignupConfigObject;

export const Config = createContext<ConfigObject | null>(null);
