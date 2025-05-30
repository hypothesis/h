import { createContext } from 'preact';

export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  csrfToken: string;
  formErrors?: Record<string, string>;
  formData?: Record<string, string>;
};

/** Return the frontend config from the page's <script class="js-config">. */
export function readConfig(): ConfigObject {
  try {
    return JSON.parse(document.querySelector('.js-config')!.textContent!);
  } catch {
    throw new Error('Failed to parse frontend configuration');
  }
}

export const Config = createContext<ConfigObject | null>(null);
