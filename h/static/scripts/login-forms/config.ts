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

/** Data passed to frontend for profile form. */
export type ProfileConfigObject = ConfigBase & {
  formErrors?: {
    display_name?: string;
    description?: string;
    location?: string;
    link?: string;
  };
  formData?: {
    display_name?: string;
    description?: string;
    location?: string;
    link?: string;
  };
};

export type ConfigObject =
  | LoginConfigObject
  | SignupConfigObject
  | ProfileConfigObject;

export const Config = createContext<ConfigObject | null>(null);
