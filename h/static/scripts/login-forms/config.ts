import { createContext } from 'preact';

export type ConfigObject = {
  csrfToken: string;
  formErrors?: Record<string, string>;
  formData?: Record<string, string>;
};

export const Config = createContext<ConfigObject | null>(null);
