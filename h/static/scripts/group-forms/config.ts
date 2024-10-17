import type { GroupType } from './utils/api';

export type APIConfig = {
  method: string;
  url: string;
  headers: Record<PropertyKey, unknown>;
};

export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  styles: string[];
  api: {
    createGroup: APIConfig;
    updateGroup: APIConfig | null;
  };
  context: {
    group: {
      pubid: string;
      name: string;
      description: string;
      link: string;
      type: GroupType;
      num_annotations: number;
    } | null;
  };
  features: {
    group_type: boolean;
  };
};

/** Return the frontend config from the page's <script class="js-config">. */
export function readConfig(): ConfigObject {
  return JSON.parse(document.querySelector('.js-config')!.textContent!);
}
