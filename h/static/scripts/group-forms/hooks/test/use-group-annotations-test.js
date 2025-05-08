import { mount, waitFor, waitForElement } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import { useGroupAnnotations, $imports } from '../use-group-annotations';

describe('useGroupAnnotations', () => {
  let fakeConfig;
  let fakeFetchGroupAnnotations;

  beforeEach(() => {
    fakeConfig = {
      api: {
        groupAnnotations: {},
      },
    };
    fakeFetchGroupAnnotations = sinon.stub().resolves([]);

    $imports.$mock({
      '../utils/api/fetch-group-annotations': {
        fetchGroupAnnotations: fakeFetchGroupAnnotations,
      },
    });
  });

  function TestComponent({ filterStatus }) {
    const { annotations, loading, error } = useGroupAnnotations({
      filterStatus,
    });

    return (
      <div>
        <div data-testid="annotation-amount">{annotations.length}</div>
        <div data-testid="loading">{loading ? 'YES' : 'NO'}</div>
        {error && <div data-testid="error">{error}</div>}
      </div>
    );
  }

  function createComponent(filterStatus) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <TestComponent filterStatus={filterStatus} />
      </Config.Provider>,
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

      const wrapper = createComponent(moderationStatus);
      await waitForElement(wrapper, '[data-testid="error"]');

      assert.calledWith(
        fakeFetchGroupAnnotations,
        {},
        sinon.match({ moderationStatus }),
      );
      assert.equal(wrapper.find('[data-testid="error"]').text(), errorMessage);
      assert.equal(wrapper.find('[data-testid="loading"]').text(), 'NO');
    });
  });

  it('sets loading before starting to fetch annotations', async () => {
    const wrapper = createComponent();

    // Loading is initially true, and eventually it is set to false
    assert.equal(wrapper.find('[data-testid="loading"]').text(), 'YES');
    await waitFor(
      () => wrapper.find('[data-testid="loading"]').text() === 'NO',
    );
  });

  const arrayOfSize = size => Array.from({ length: size }).map(() => ({}));

  [arrayOfSize(5), arrayOfSize(50), arrayOfSize(1)].forEach(annotations => {
    it('sets annotations as resolved by fetchGroupAnnotations', async () => {
      fakeFetchGroupAnnotations.resolves(annotations);
      const wrapper = createComponent();

      // The amount of annotations is initially 0, and then eventually changes
      // to the loaded ones
      assert.equal(
        wrapper.find('[data-testid="annotation-amount"]').text(),
        '0',
      );
      await waitFor(
        () =>
          wrapper.find('[data-testid="annotation-amount"]').text() ===
          `${annotations.length}`,
      );
    });
  });
});
