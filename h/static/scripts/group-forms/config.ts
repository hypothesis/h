export type APIConfig = {
  method: string;
  url: string;
  headers: object;
};

export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  styles: string[];
  api: {
    createGroup: APIConfig;
  };
};

/** Return the frontend config from the page's <script class="js-config">. */
export function readConfig(): ConfigObject {
  return JSON.parse(document.querySelector('.js-config')!.textContent!);
}
