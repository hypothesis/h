import { createContext } from 'preact';

export type ConfigObject = {
  csrfToken: string;
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
  forOAuth?: boolean;
};

export const Config = createContext<ConfigObject | null>(null);
