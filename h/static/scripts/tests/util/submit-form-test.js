import { submitForm } from '../../util/submit-form';
import { unroll } from '../util';

function createResponse(status, body) {
  let statusText;
  if (status === 500) {
    statusText = 'Internal Server Error';
  }
  return {
    status,
    statusText,
    text: sinon.stub().resolves(body),
  };
}

describe('submitForm', () => {
  const FORM_URL = 'http://example.org/things';

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
      const fetchMock = sinon
        .stub()
        .withArgs(testCase.expectedSubmitUrl)
        .resolves(createResponse(200, '<form><!-- updated form !--></form>'));

      return submitForm(form, fetchMock).then(() => {
        assert.equal(fetchMock.callCount, 1);
        const requestInit = fetchMock.getCall(0).args[1];
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
    const fetchMock = sinon.stub().resolves(createResponse(200, responseBody));

    return submitForm(form, fetchMock).then(response => {
      assert.equal(response.form, responseBody);
    });
  });

  it('rejects with the updated form markup if validation fails', () => {
    const form = createForm();
    const fetchMock = sinon.stub().resolves(createResponse(400, 'response'));

    const done = submitForm(form, fetchMock);

    return done.catch(err => {
      assert.match(err, sinon.match({ status: 400, form: 'response' }));
    });
  });

  it('rejects with an error message if submission fails', () => {
    const form = createForm();
    const fetchMock = sinon.stub().resolves(createResponse(500));

    const done = submitForm(form, fetchMock);

    return done.catch(err => {
      assert.match(
        err,
        sinon.match({ status: 500, reason: 'Internal Server Error' }),
      );
    });
  });
});
