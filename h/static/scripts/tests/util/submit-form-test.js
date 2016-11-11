'use strict';

const fetchMock = require('fetch-mock');

const submitForm = require('../../util/submit-form');

describe('submitForm', () => {
  const FORM_URL = 'http://example.org/things';

  function mockResponse(response) {
    fetchMock.post(FORM_URL, response);
  }

  function createForm() {
    const form = document.createElement('form');
    form.action = FORM_URL;
    form.method = 'POST';
    form.innerHTML = '<input name="field" value="value">';
    return form;
  }

  it('submits the form data', () => {
    const form = createForm();
    mockResponse('<form><!-- updated form !--></form>');

    return submitForm(form, fetchMock.fetchMock).then(() => {
      const [,requestInit] = fetchMock.lastCall(FORM_URL);
      assert.instanceOf(requestInit.body, FormData);
    });
  });

  it('returns the markup for the updated form if validation succeeds', () => {
    const form = createForm();
    const responseBody = '<form><!-- updated form !--></form>';
    mockResponse(responseBody);

    return submitForm(form, fetchMock.fetchMock).then((response) => {
      assert.equal(response.form, responseBody);
    });
  });

  it('rejects with the updated form markup if validation fails', () => {
    const form = createForm();
    mockResponse({status: 400, body: 'response'});

    const done = submitForm(form, fetchMock.fetchMock);

    return done.catch((err) => {
      assert.match(err, sinon.match({status: 400, form: 'response'}));
    });
  });

  it('rejects with an error message if submission fails', () => {
    const form = createForm();
    mockResponse({status: 500, statusText: 'Internal Server Error'});

    const done = submitForm(form, fetchMock.fetchMock);

    return done.catch((err) => {
      assert.match(err, sinon.match({status: 500, reason: 'Internal Server Error'}));
    });
  });
});
