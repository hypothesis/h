import { createContext } from 'preact';

type Organization = {
  label: string;
  pubid: string;
};

type Group = {
  type?: string;
  name?: string;
  organization?: string;
  creator?: string;
  description?: string;
  enforceScope?: boolean;
  scopes?: string[];
  members?: string[];
};

type Errors = {
  type?: string;
  name?: string;
};

export type ConfigObject = {
  styles: string[]; // The URLs of the app's CSS stylesheets.
  CSRFToken: string; // The CSRF token that must be included in form submissions.
  context: {
    organizations: Organization[];
    defaultOrganization: Organization;
    group: Group;
    user: {
      username: string;
    };
    errors: Errors;
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
