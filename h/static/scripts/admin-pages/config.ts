import { createContext } from 'preact';

type Organization = {
  label: string;
  pubid: string;
};

type Group = null;

export type ConfigObject = {
  styles: string[]; // The URLs of the app's CSS stylesheets.
  CSRFToken: string; // The CSRF token that must be included in form submissions.
  context: {
    organizations: Organization[];
    defaultOrganization: Organization;
    group: Group | null;
    user: {
      username: string;
    };
  };
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
