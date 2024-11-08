import { createContext } from 'preact';
import type { GroupType } from './utils/api';

export type APIConfig = {
  method: string;
  url: string;
  headers: Record<PropertyKey, unknown>;
};

export type Group = {
  pubid: string;
  name: string;
  description: string;
  link: string;
  type: GroupType;
  num_annotations: number;
};

export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  styles: string[];
  api: {
    createGroup: APIConfig;
    updateGroup: APIConfig | null;
  };
  context: {
    group: Group | null;
  };
  features: {
    group_members: boolean;
    group_type: boolean;
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
