import { mount, waitFor } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import {
  useUpdateModerationStatus,
  $imports,
} from '../use-update-moderation-status';

describe('useUpdateModerationStatus', () => {
  let fakeConfig;
  let fakeAnnotation;
  let fakeCallAPI;
  let lastUpdateModerationStatus;

  beforeEach(() => {
    fakeConfig = { api: {} };
    fakeAnnotation = {
      id: '1',
      updated: '2025-06-24T08:43:50.914807+00:00',
    };

    fakeCallAPI = sinon.stub();

    $imports.$mock({
      '../utils/api': { callAPI: fakeCallAPI },
    });

    lastUpdateModerationStatus = undefined;
  });

  function TestComponent({ annotation }) {
    lastUpdateModerationStatus = useUpdateModerationStatus(annotation);
    return null;
  }

  function createComponent(annotation = fakeAnnotation) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <TestComponent annotation={annotation} />
      </Config.Provider>,
    );
  }

  it('does not call API if config is not available', () => {
    createComponent();
    lastUpdateModerationStatus.updateModerationStatus('APPROVED');

    assert.notCalled(fakeCallAPI);
  });

  it('does not call API if annotation does not have an ID', () => {
    fakeConfig.api.annotationModeration = {};
    createComponent({});

    lastUpdateModerationStatus.updateModerationStatus('APPROVED');

    assert.notCalled(fakeCallAPI);
  });

  ['PENDING', 'APPROVED', 'DENIED', 'SPAM'].forEach(moderationStatus => {
    it('calls APi if config and annotation ID are available', async () => {
      const { promise: apiCallPromise, resolve } = Promise.withResolvers();
      fakeCallAPI.returns(apiCallPromise);
      fakeConfig.api.annotationModeration = {
        url: 'https://example.com/:annotationId',
      };
      createComponent();

      lastUpdateModerationStatus.updateModerationStatus(moderationStatus);

      // `updating` is set to `true` when starting the request
      await waitFor(() => lastUpdateModerationStatus.updating);
      assert.calledWith(
        fakeCallAPI,
        `https://example.com/${fakeAnnotation.id}`,
        sinon.match({
          json: {
            annotation_updated: fakeAnnotation.updated,
            moderation_status: moderationStatus,
          },
        }),
      );

      // Once promise settles, `updating` is set to false
      resolve(undefined);
      await apiCallPromise;
      await waitFor(() => !lastUpdateModerationStatus.updating);
    });
  });

  it('aborts previous request when a second one is triggered', async () => {
    fakeConfig.api.annotationModeration = {
      url: 'https://example.com/:annotationId',
    };
    createComponent();

    await lastUpdateModerationStatus.updateModerationStatus('PENDING');
    await lastUpdateModerationStatus.updateModerationStatus('APPROVED');

    assert.equal(fakeCallAPI.callCount, 2);
    const firstAPICall = fakeCallAPI.getCall(0);
    const secondAPICall = fakeCallAPI.getCall(1);

    // The first callAPI should have an aborted signal, while the second one
    // should not
    assert.isTrue(firstAPICall.args[1].signal.aborted);
    assert.isFalse(secondAPICall.args[1].signal.aborted);
  });
});
