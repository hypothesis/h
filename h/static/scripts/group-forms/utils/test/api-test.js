import { callAPI, APIError, paginationToParams } from '../api';

describe('callAPI', () => {
  const url = 'https://api.example.com/foo';
  let fakeFetch;

  beforeEach(() => {
    fakeFetch = sinon.stub(window, 'fetch');
  });

  afterEach(() => {
    window.fetch.restore?.();
  });

  context('when the API responds successfully', () => {
    const responseBody = { foo: 'bar' };

    beforeEach(() => {
      fakeFetch
        .withArgs(url)
        .resolves(new Response(JSON.stringify(responseBody), { status: 200 }));
    });

    it('makes a request for the given URL', async () => {
      await callAPI(url);

      assert.ok(
        fakeFetch.calledOnceWith(
          url,
          sinon.match({
            method: 'GET',
            headers: {
              'Content-Type': 'application/json; charset=UTF-8',
            },
          }),
        ),
      );
    });

    for (const method of ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']) {
      context(`when the request method is ${method}`, () => {
        it('makes a request using the given method', async () => {
          await callAPI(url, { method });

          assert.equal(fakeFetch.lastCall.args[1].method, method);
        });
      });
    }

    it('makes a request with the given JSON body', async () => {
      const json = { foo: 'bar' };

      await callAPI(url, { method: 'POST', json });

      assert.equal(fakeFetch.lastCall.args[1].body, JSON.stringify(json));
    });

    it('makes a request with the given headers', async () => {
      const headers = { foo: 'bar' };

      await callAPI(url, { method: 'POST', headers });

      headers['Content-Type'] = 'application/json; charset=UTF-8';
      assert.deepEqual(fakeFetch.lastCall.args[1].headers, headers);
    });

    it('returns the parsed JSON object', async () => {
      const result = await callAPI(url);

      assert.deepEqual(result, responseBody);
    });

    it('supports 204 (empty) responses', async () => {
      const response = new Response(null, { status: 204 });
      fakeFetch.withArgs(url).resolves(response);

      const result = await callAPI(url);

      assert.deepEqual(result, {});
    });

    it("throws an error when the response body isn't valid json", async () => {
      const response = new Response('not valid JSON', { status: 200 });
      sinon.spy(response, 'json');
      fakeFetch.withArgs(url).resolves(response);

      let error;
      try {
        await callAPI(url);
      } catch (err) {
        error = err;
      }

      let cause;
      try {
        await response.json.returnValues[0];
      } catch (err) {
        cause = err;
      }

      assert.instanceOf(error, APIError);
      assert.equal(error.message, 'Invalid API response.');
      assert.equal(error.cause, cause);
      assert.equal(error.response, response);
      assert.equal(error.json, null);
    });
  });

  it('re-throws the error from fetch() when the API fails to get a response', async () => {
    const cause = new TypeError();
    fakeFetch.withArgs(url).rejects(cause);
    let error;

    try {
      await callAPI(url);
    } catch (err) {
      error = err;
    }

    assert.instanceOf(error, APIError);
    assert.equal(error.message, 'Network request failed.');
    assert.equal(error.cause, cause);
    assert.equal(error.response, null);
    assert.equal(error.json, null);
  });

  it('adds query params to URL', async () => {
    const paginatedURL = new URL(url);
    const pageNumber = 5;
    const pageSize = 10;
    paginatedURL.searchParams.set('pageNumber', pageNumber);
    paginatedURL.searchParams.set('pageSize', pageSize);
    const response = new Response(JSON.stringify({}), { status: 200 });
    fakeFetch.resolves(response);

    await callAPI(url, {
      query: { pageNumber, pageSize },
    });

    assert.calledWith(fakeFetch, paginatedURL.toString());
  });

  it('rejects with aborted APIError if request is aborted', async () => {
    window.fetch.restore();

    const ac = new AbortController();
    ac.abort();

    let error;
    try {
      await callAPI(url, { signal: ac.signal });
    } catch (e) {
      error = e;
    }

    assert.instanceOf(error, APIError);
    assert.isTrue(error.aborted);
  });

  [
    {
      response: new Response(
        JSON.stringify({ reason: 'Error message from server.' }),
        { status: 403 },
      ),
      json: { reason: 'Error message from server.' },
      message: 'Error message from server.',
    },
    {
      response: new Response(JSON.stringify({ foo: 'bar' }), { status: 400 }),
      json: { foo: 'bar' },
      message: 'API request failed.',
    },
    {
      response: new Response(JSON.stringify([]), { status: 401 }),
      json: [],
      message: 'API request failed.',
    },
    {
      response: new Response('not valid json', { status: 500 }),
      json: null,
      message: 'API request failed.',
    },
  ].forEach(({ response, json, message }) => {
    it('throws an error when the API responds with an error', async () => {
      fakeFetch.withArgs(url).resolves(response);
      let error;

      try {
        await callAPI(url);
      } catch (err) {
        error = err;
      }

      assert.instanceOf(error, APIError);
      assert.equal(error.message, message);
      assert.equal(error.cause, null);
      assert.equal(error.response, response);
      assert.deepEqual(error.json, json);
    });
  });
});

describe('paginationToParams', () => {
  [
    {
      expectedQuery: {},
    },
    {
      pageNumber: 1,
      expectedQuery: { 'page[number]': 1 },
    },
    {
      pageSize: 30,
      expectedQuery: { 'page[size]': 30 },
    },
    {
      pageNumber: 5,
      pageSize: 10,
      expectedQuery: { 'page[number]': 5, 'page[size]': 10 },
    },
  ].forEach(({ pageNumber, pageSize, expectedQuery }) => {
    it('converts pagination values to query params', () => {
      assert.deepEqual(
        paginationToParams({ pageNumber, pageSize }),
        expectedQuery,
      );
    });
  });
});
