/** Data for an HTML form. */
export type FormFields<Fields> = {
  /** Initial values for the form fields. */
  data?: Fields;

  /** Validation errors associated with individual fields. */
  errors?: Record<keyof Fields, string>;
};

/** Return the frontend config from the page's <script class="js-config">. */
export function readConfig<T>(): T {
  try {
    return JSON.parse(document.querySelector('.js-config')!.textContent!);
  } catch {
    throw new Error('Failed to parse frontend configuration');
  }
}

/**
 * Find the DOM container element for a Preact application or throw an error.
 *
 * The purpose of this utility is to generate a more helpful error if the
 * container element is missing.
 */
export function findContainer(selector: string): Element {
  const container = document.querySelector(selector);
  if (!container) {
    throw new Error(
      `Unable to render UI because container "${selector}" was not found`,
    );
  }
  return container;
}
