/** Return the frontend config from the page's <script class="js-config">. */
export function readConfig<T>(): T {
  try {
    return JSON.parse(document.querySelector('.js-config')!.textContent!);
  } catch {
    throw new Error('Failed to parse frontend configuration');
  }
}

