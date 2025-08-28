import { fetchGroupAnnotations, $imports } from '../fetch-group-annotations';

describe('fetch-group-annotations', () => {
  let fakeCallAPI;

  beforeEach(() => {
    fakeCallAPI = sinon.stub().resolves({
      data: [],
      meta: {
        page: { total: 0 },
      },
    });

    $imports.$mock({
      '.': {
        callAPI: fakeCallAPI,
      },
    });
  });

  [
    {
      after: '2025-05-21T14:02:07.509098+00:00',
      pageSize: 20,
      moderationStatus: 'APPROVED',
      expectedQuery: {
        'page[after]': '2025-05-21T14:02:07.509098+00:00',
        'page[size]': 20,
        moderation_status: 'APPROVED',
      },
    },
    {
      moderationStatus: 'SPAM',
      expectedQuery: {
        'page[size]': 20,
        moderation_status: 'SPAM',
      },
    },
    {
      after: '2025-05-01T14:02:07.509098+00:00',
      pageSize: 6,
      expectedQuery: {
        'page[after]': '2025-05-01T14:02:07.509098+00:00',
        'page[size]': 6,
      },
    },
    {
      expectedQuery: {
        'page[size]': 20,
      },
    },
  ].forEach(({ after, pageSize = 20, moderationStatus, expectedQuery }) => {
    it('calls API with expected parameters', async () => {
      const { signal } = new AbortController();

      await fetchGroupAnnotations(
        {
          url: '/api/groups/abc123/annotations',
          method: 'GET',
          headers: {},
        },
        { signal, after, pageSize, moderationStatus },
      );

      assert.calledWith(fakeCallAPI, '/api/groups/abc123/annotations', {
        signal,
        query: expectedQuery,
        method: 'GET',
        headers: {},
      });
    });
  });
});
