export type ConfigObject = {
  /** The URLs of the app's CSS stylesheets. */
  styles: string[];
};

/** Return the frontend config from the page's <script class="js-config">. */
export default function readConfig(): ConfigObject {
  return JSON.parse(document.querySelector('.js-config')!.textContent!);
}
