import { delay, mount, waitFor } from '@hypothesis/frontend-testing';
import { useState } from 'preact/hooks';

import { GroupFormsConfig } from '../../config';
import { useGroupAnnotations, $imports } from '../use-group-annotations';

describe('useGroupAnnotations', () => {
  let fakeConfig;
  let fakeFetchGroupAnnotations;
  let lastGroupAnnotations;

  beforeEach(() => {
    fakeConfig = {
      api: {
        groupAnnotations: {},
      },
    };
    fakeFetchGroupAnnotations = sinon.stub().resolves({ annotations: [] });
    lastGroupAnnotations = undefined;

    $imports.$mock({
      '../util/api/fetch-group-annotations': {
        fetchGroupAnnotations: fakeFetchGroupAnnotations,
      },
    });
  });

  function TestComponent({ initialFilterStatus }) {
    const [filterStatus, setFilterStatus] = useState(initialFilterStatus);
    lastGroupAnnotations = useGroupAnnotations({ filterStatus });

    return (
      <button
        data-testid="set-status-button"
        onClick={() => setFilterStatus('APPROVED')}
      >
        Set status
      </button>
    );
  }

  function createComponent(filterStatus) {
    return mount(
      <GroupFormsConfig.Provider value={fakeConfig}>
        <TestComponent initialFilterStatus={filterStatus} />
      </GroupFormsConfig.Provider>,
    );
  }

  [null, { api: {} }].forEach(config => {
    it('throws if groupAnnotations API info is not available', () => {
      fakeConfig = config;
      let error;

      try {
        createComponent();
      } catch (e) {
        error = e;
      }

      assert.equal(error?.message, 'groupAnnotations API config missing');
    });
  });

  ['PENDING', 'APPROVED', 'DENIED', 'SPAM'].forEach(moderationStatus => {
    it('sets error when fetchGroupAnnotations rejects', async () => {
      const errorMessage = 'Something went wrong';
      fakeFetchGroupAnnotations.rejects(new Error(errorMessage));

      createComponent(moderationStatus);

      assert.calledWith(
        fakeFetchGroupAnnotations,
        {},
        sinon.match({ moderationStatus }),
      );

      await waitFor(() => lastGroupAnnotations.error === errorMessage);
      assert.isFalse(lastGroupAnnotations.loading);
    });
  });

  it('sets loading before starting to fetch annotations', async () => {
    createComponent();

    // Loading is initially true, and eventually it is set to false
    assert.isTrue(lastGroupAnnotations.loading);
    await waitFor(() => !lastGroupAnnotations.loading);
  });

  const arrayOfSize = size => Array.from({ length: size }, () => ({}));

  [arrayOfSize(5), arrayOfSize(50), arrayOfSize(1)].forEach(annotations => {
    it('sets annotations as resolved by fetchGroupAnnotations', async () => {
      fakeFetchGroupAnnotations.resolves({ annotations });
      createComponent();

      // The annotations are initially not set, and then eventually change to
      // the loaded ones
      assert.isUndefined(lastGroupAnnotations.annotations);
      await waitFor(
        () =>
          lastGroupAnnotations.annotations &&
          lastGroupAnnotations.annotations.length === annotations.length,
      );
    });
  });

  it('fetches next page every time loadNextPage is called', async () => {
    // A total of 60 items, with 20 items per page, means we won't call this
    // more than three times
    fakeFetchGroupAnnotations.resolves({
      annotations: arrayOfSize(20),
      total: 60,
    });

    const invokeLoadNextPage = async () => {
      // We have to wait for previous call to finish loading before invoking it
      // again
      await waitFor(() => !lastGroupAnnotations.loading);
      lastGroupAnnotations.loadNextPage();
    };

    createComponent();

    // First page is loaded automatically
    assert.calledWith(
      fakeFetchGroupAnnotations.lastCall,
      {},
      sinon.match({ pageNumber: 1 }),
    );
    assert.equal(fakeFetchGroupAnnotations.callCount, 1);

    // Subsequent calls will increase the page number
    await invokeLoadNextPage();
    assert.calledWith(
      fakeFetchGroupAnnotations.lastCall,
      {},
      sinon.match({ pageNumber: 2 }),
    );
    assert.equal(fakeFetchGroupAnnotations.callCount, 2);

    await invokeLoadNextPage();
    assert.calledWith(
      fakeFetchGroupAnnotations.lastCall,
      {},
      sinon.match({ pageNumber: 3 }),
    );
    assert.equal(fakeFetchGroupAnnotations.callCount, 3);

    // Once all pages have been loaded, calling loadNextPage has no effect
    await invokeLoadNextPage();
    assert.equal(fakeFetchGroupAnnotations.callCount, 3);
    await invokeLoadNextPage();
    assert.equal(fakeFetchGroupAnnotations.callCount, 3);
  });

  it('resets loaded annotations when the filter status changes', async () => {
    const annotations = arrayOfSize(3);
    fakeFetchGroupAnnotations.resolves({ annotations });

    const wrapper = createComponent('PENDING');
    await waitFor(() => !lastGroupAnnotations.loading);

    assert.lengthOf(lastGroupAnnotations.annotations, annotations.length);
    wrapper.find('[data-testid="set-status-button"]').simulate('click');
    assert.isUndefined(lastGroupAnnotations.annotations);
  });

  context('when moderation status is changed', () => {
    it('updates annotation status when no filter status is set', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
        { id: '789', moderation_status: 'DENIED' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent();
      await waitFor(() => !lastGroupAnnotations.loading);

      lastGroupAnnotations.updateAnnotationStatus('456', 'APPROVED');

      // Wait for next tick so that state changes are applied
      await delay(0);
      assert.deepEqual(
        [
          { id: '123', moderation_status: 'PENDING' },
          { id: '456', moderation_status: 'APPROVED' },
          { id: '789', moderation_status: 'DENIED' },
        ],
        lastGroupAnnotations.annotations,
      );
    });

    it('updates annotation status and keeps it in list when status does not match filter', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent('PENDING');
      await waitFor(() => !lastGroupAnnotations.loading);

      lastGroupAnnotations.updateAnnotationStatus('456', 'APPROVED');
      await delay(0);

      // Annotation should still be in the list but with updated status
      assert.deepEqual(
        [
          { id: '123', moderation_status: 'PENDING' },
          { id: '456', moderation_status: 'APPROVED' },
        ],
        lastGroupAnnotations.annotations,
      );
    });

    it('marks annotation as removed when new status does not match filter', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent('PENDING');
      await waitFor(() => !lastGroupAnnotations.loading);

      lastGroupAnnotations.updateAnnotationStatus('456', 'APPROVED');

      await delay(0);

      assert.isTrue(lastGroupAnnotations.removedAnnotations.has('456'));
      assert.isFalse(lastGroupAnnotations.removedAnnotations.has('123'));
    });

    it('does not mark annotation as removed when new status matches filter', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent('PENDING');
      await waitFor(() => !lastGroupAnnotations.loading);

      // Change status to same as filter
      lastGroupAnnotations.updateAnnotationStatus('456', 'PENDING');
      await delay(0);

      // Annotation should not be marked as removed
      assert.equal(lastGroupAnnotations.removedAnnotations.size, 0);
    });

    it('does not mark annotation as removed when no filter is set', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent(); // No filter status
      await waitFor(() => !lastGroupAnnotations.loading);

      lastGroupAnnotations.updateAnnotationStatus('456', 'APPROVED');
      await delay(0);

      assert.equal(lastGroupAnnotations.removedAnnotations.size, 0);
    });

    it('does not update any annotations when an unknown ID is provided', async () => {
      const annotations = [
        { id: '123', moderation_status: 'PENDING' },
        { id: '456', moderation_status: 'PENDING' },
      ];
      fakeFetchGroupAnnotations.resolves({ annotations });

      createComponent(); // No filter status
      await waitFor(() => !lastGroupAnnotations.loading);

      lastGroupAnnotations.updateAnnotationStatus('unknown-id', 'APPROVED');
      await delay(0);

      assert.deepEqual(lastGroupAnnotations.annotations, annotations);
    });
  });

  it('returns empty `removedAnnotations` set if no annotations have been removed', async () => {
    createComponent();
    assert.equal(lastGroupAnnotations.removedAnnotations.size, 0);
  });

  it('clears `removedAnnotations` when filter status changes', async () => {
    const annotations = [
      { id: '123', moderation_status: 'PENDING' },
      { id: '456', moderation_status: 'PENDING' },
    ];
    fakeFetchGroupAnnotations.resolves({ annotations });

    const wrapper = createComponent('PENDING');
    await waitFor(() => !lastGroupAnnotations.loading);

    lastGroupAnnotations.updateAnnotationStatus('456', 'APPROVED');
    await delay(0);
    assert.isTrue(lastGroupAnnotations.removedAnnotations.has('456'));

    // Change filter status
    wrapper.find('[data-testid="set-status-button"]').simulate('click');

    assert.equal(lastGroupAnnotations.removedAnnotations.size, 0);
  });
});
