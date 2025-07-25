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

/** Data passed to frontend for signup form. */
export type SignupConfigObject = ConfigBase & {
  features: {
    log_in_with_orcid: boolean;
    log_in_with_google: boolean;
  };
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

export type SignupWithORCIDConfigObject = ConfigBase & {
  identity: { provider_unique_id: string };
  features: {
    log_in_with_orcid: boolean;
  };
  formErrors?: {
    username?: string;
    email?: string;
    privacy_accepted?: string;
  };
  formData?: {
    idinfo?: string;
    username: string;
    email: string;
    privacy_accepted: boolean;
    comms_opt_in: boolean;
  };
};

export type SignupWithGoogleConfigObject = ConfigBase & {
  identity: { provider_unique_id: string };
  features: {
    log_in_with_google: boolean;
  };
  formErrors?: {
    username?: string;
    email?: string;
    privacy_accepted?: string;
  };
  formData?: {
    idinfo?: string;
    username: string;
    email: string;
    privacy_accepted: boolean;
    comms_opt_in: boolean;
  };
};

export type ConfigObject = LoginConfigObject | SignupConfigObject;

export const Config = createContext<ConfigObject | null>(null);
