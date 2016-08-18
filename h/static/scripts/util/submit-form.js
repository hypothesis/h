'use strict';

/**
 * Submit a form using XMLHttpRequest and update the rendered form with the
 * response HTML.
 *
 * @param {HTMLFormElement} formEl - The `<form>` to submit
 * @return {Promise} A promise which resolves when the form submission completes
 */
function submitForm(formEl, XMLHttpRequest) {
  XMLHttpRequest = XMLHttpRequest || window.XMLHttpRequest;

  var formData = new FormData(formEl);
  var req = new XMLHttpRequest();
  req.open('POST', formEl.action, true /* async */);

  // Flag this as an XHR request so that the server can respond accordingly
  req.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

  req.send(formData);

  return new Promise(function (resolve, reject) {
    req.onreadystatechange = function () {
      if (req.readyState === XMLHttpRequest.DONE) {
        if (req.status === 200) {
          resolve({status: req.status, form: req.responseText});
        } else {
          reject({status: req.status, form: req.responseText});
        }
      }
    };
  });
}

module.exports = submitForm;
