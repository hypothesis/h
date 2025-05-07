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
  pre_moderated: boolean;
};

export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  styles: string[];
  api: {
    createGroup: APIConfig;
    updateGroup?: APIConfig;
    readGroupMembers?: APIConfig;
    editGroupMember?: APIConfig;
    removeGroupMember?: APIConfig;
    groupAnnotations?: APIConfig;
  };
  context: {
    group: Group | null;
    user: {
      userid: string;
    };
  };
  features: {
    group_members: boolean;
    group_type: boolean;
    group_moderation: boolean;
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
