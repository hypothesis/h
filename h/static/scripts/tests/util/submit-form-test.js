import fetchMock from 'fetch-mock';

import { submitForm } from '../../util/submit-form';
import { unroll } from '../util';

describe('submitForm', () => {
  const FORM_URL = 'http://example.org/things';

  afterEach(() => {
    fetchMock.restore();
  });

  function mockResponse(response, url = FORM_URL) {
    fetchMock.post(url, response);
  }

  function createForm() {
    const form = document.createElement('form');
    form.action = FORM_URL;
    form.method = 'POST';
    form.innerHTML = '<input name="field" value="value">';
    return form;
  }

  unroll(
    'submits the form data',
    testCase => {
      const form = document.createElement('form');
      form.method = 'POST';
      form.innerHTML = '<input name="field" value="value">';

      if (typeof testCase.action === 'string') {
        form.setAttribute('action', testCase.action);
      }
      mockResponse(
        '<form><!-- updated form !--></form>',
        testCase.expectedSubmitUrl,
      );

      return submitForm(form, fetchMock.fetchMock).then(() => {
        const [, requestInit] = fetchMock.lastCall(testCase.expectedSubmitUrl);
        assert.instanceOf(requestInit.body, FormData);
      });
    },
    [
      {
        action: FORM_URL,
        expectedSubmitUrl: FORM_URL,
      },
      {
        // Setting "action" to an empty string is technically disallowed according
        // to https://w3c.github.io/html/sec-forms.html#element-attrdef-form-action
        // but in practice browsers treat it mostly the same way as a missing
        // "action" attr.
        action: '',
        expectedSubmitUrl: document.location.href,
      },
      {
        // Omit "action" attr.
        action: null,
        expectedSubmitUrl: document.location.href,
      },
    ],
  );

  it('returns the markup for the updated form if validation succeeds', () => {
    const form = createForm();
    const responseBody = '<form><!-- updated form !--></form>';
    mockResponse(responseBody);

    return submitForm(form, fetchMock.fetchMock).then(response => {
      assert.equal(response.form, responseBody);
    });
  });

  it('rejects with the updated form markup if validation fails', () => {
    const form = createForm();
    mockResponse({ status: 400, body: 'response' });

    const done = submitForm(form, fetchMock.fetchMock);

    return done.catch(err => {
      assert.match(err, sinon.match({ status: 400, form: 'response' }));
    });
  });

  it('rejects with an error message if submission fails', () => {
    const form = createForm();
    mockResponse({ status: 500, statusText: 'Internal Server Error' });

    const done = submitForm(form, fetchMock.fetchMock);

    return done.catch(err => {
      assert.match(
        err,
        sinon.match({ status: 500, reason: 'Internal Server Error' }),
      );
    });
  });
});
