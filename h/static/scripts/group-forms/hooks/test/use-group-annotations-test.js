import { mount, waitFor } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
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
    fakeFetchGroupAnnotations = sinon.stub().resolves([]);
    lastGroupAnnotations = undefined;

    $imports.$mock({
      '../utils/api/fetch-group-annotations': {
        fetchGroupAnnotations: fakeFetchGroupAnnotations,
      },
    });
  });

  function TestComponent({ filterStatus }) {
    lastGroupAnnotations = useGroupAnnotations({ filterStatus });
  }

  function createComponent(filterStatus) {
    mount(
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
      fakeFetchGroupAnnotations.resolves(annotations);
      createComponent();

      // The amount of annotations is initially 0, and then eventually changes
      // to the loaded ones
      assert.lengthOf(lastGroupAnnotations.annotations, 0);
      await waitFor(
        () => lastGroupAnnotations.annotations.length === annotations.length,
      );
    });
  });
});
