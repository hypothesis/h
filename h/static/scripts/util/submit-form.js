'use strict';

/**
 * @typedef SubmitError
 * @property {number} status - HTTP status code. 400 if form submission failed
 *           due to a validation error or a different 4xx or 5xx code if it
 *           failed for other reasons.
 * @property {string} [form] - HTML markup for the form containing validation
 *           error messages if submission failed with a 400 status.
 * @property {string} [reason] - The status message if form submission failed
 *           for reasons other than a validation error.
 */

/**
 * Exception thrown if form submission fails.
 *
 * @property {SubmitError} params - Describes why submission failed. These
 *           properties are exposed on the FormSubmitError instance.
 */
class FormSubmitError extends Error {
  constructor(message, params) {
    super(message);
    Object.assign(this, params);
  }
}

/**
 * @typedef {Object} SubmitResult
 * @property {number} status - Always 200
 * @property {string} form - The HTML markup for the re-rendered form
 */

/**
 * Submit a form using the Fetch API and return the markup for the re-rendered
 * version of the form.
 *
 * @param {HTMLFormElement} formEl - The `<form>` to submit
 * @return {Promise<SubmitResult>} A promise which resolves when the form
 *         submission completes or rejects with a FormSubmitError if the server
 *         rejects the submission due to a validation error or the network
 *         request fails.
 */
function submitForm(formEl, fetch = window.fetch) {
  let response;
  return fetch(formEl.action, {
    body: new FormData(formEl),
    credentials: 'same-origin',
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
  }).then((response_) => {
    response = response_;
    return response.text();
  }).then((body) => {
    const { status } = response;
    switch (status) {
    case 200:
      return {status, form: body};
    case 400:
      throw new FormSubmitError('Form validation failed', {
        status, form: body,
      });
    default:
      throw new FormSubmitError('Form submission failed', {
        status,
        reason: response.statusText,
      });
    }
  });
}

module.exports = submitForm;
