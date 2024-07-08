/**
 * This module configures Sentry crash reporting.
 *
 * Logging requires the Sentry DSN and Hypothesis version to be provided via the
 * app's settings object.
 */

import * as Sentry from '@sentry/browser';

export type SentryConfig = {
  dsn: string;
  environment: string;
  release: string;
  userid?: string;
};

export function init(config: SentryConfig) {
  Sentry.init({
    dsn: config.dsn,
    environment: config.environment,
    release: config.release,
  });

  if (config.userid) {
    Sentry.setUser({ id: config.userid });
  }
}

/**
 * Report an error to Sentry.
 *
 * @param error - An error object describing what went wrong
 * @param when - A string describing the context in which
 *                        the error occurred.
 * @param context - A JSON-serializable object containing additional
 *   information which may be useful when investigating the error.
 */
export function report(error: unknown, when: string, context?: unknown) {
  if (!(error instanceof Error)) {
    // If the passed object is not an Error, Sentry will serialize it using
    // toString() which produces unhelpful results for objects that do not
    // provide their own toString() implementations.
    //
    // If the error is a plain object or non-Error subclass with a message
    // property, such as errors returned by chrome.extension.lastError,
    // use that instead.
    if (typeof error === 'object' && error && 'message' in error) {
      error = error.message;
    }
  }

  const extra = Object.assign({ when }, context);
  Sentry.captureException(error, { extra });
}
