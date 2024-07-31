import { mount } from 'enzyme';
import { waitForElement } from '@hypothesis/frontend-testing';

import { $imports, default as CreateGroupForm } from '../CreateGroupForm';

const config = {
  api: {
    createGroup: {
      method: 'POST',
      url: 'https://example.com/api/groups',
    },
  },
};

describe('CreateGroupForm', () => {
  let fakeCallAPI;
  let fakeSetLocation;

  beforeEach(() => {
    fakeCallAPI = sinon.stub();
    fakeSetLocation = sinon.stub();

    $imports.$mock({
      '../config': { readConfig: () => config },
      '../utils/api': {
        callAPI: fakeCallAPI,
      },
      '../utils/set-location': {
        setLocation: fakeSetLocation,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  /* Return true if counterEl is in its error state. */
  const counterIsInErrorState = counterEl => {
    return (
      counterEl.hasClass('text-red-error') && counterEl.hasClass('font-bold')
    );
  };

  /* Return true if component is in its error state. */
  const componentIsInErrorState = component => {
    return Boolean(component.prop('error'));
  };

  const getElements = wrapper => {
    return {
      name: {
        counterEl: wrapper.find('[data-testid="charcounter-name"]'),
        fieldComponent: wrapper.find('Input[data-testid="name"]'),
        fieldEl: wrapper.find('input[data-testid="name"]'),
      },
      description: {
        counterEl: wrapper.find('[data-testid="charcounter-description"]'),
        fieldComponent: wrapper.find('Textarea[data-testid="description"]'),
        fieldEl: wrapper.find('textarea[data-testid="description"]'),
      },
    };
  };

  const createWrapper = () => {
    const wrapper = mount(<CreateGroupForm />);
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  [
    {
      field: 'name',
      maxLength: 25,
    },
    {
      field: 'description',
      maxLength: 250,
    },
  ].forEach(({ field, maxLength }) => {
    describe(`${field} character counter`, () => {
      it('renders a character counter', () => {
        const { counterEl, fieldComponent } = createWrapper().elements[field];

        assert.equal(counterEl.text(), `0/${maxLength}`);
        assert.isNotOk(counterIsInErrorState(counterEl));
        assert.isNotOk(componentIsInErrorState(fieldComponent));
      });

      it("changes the count when the field's text changes", () => {
        const { wrapper, elements } = createWrapper();
        const fieldEl = elements[field].fieldEl;

        fieldEl.getDOMNode().value = 'new text';
        fieldEl.simulate('input');

        const { counterEl, fieldComponent } = getElements(wrapper)[field];
        assert.equal(counterEl.text(), `8/${maxLength}`);
        assert.isNotOk(counterIsInErrorState(counterEl));
        assert.isNotOk(componentIsInErrorState(fieldComponent));
      });

      it('goes into an error state when too many characters are entered', () => {
        const { wrapper, elements } = createWrapper();
        const fieldEl = elements[field].fieldEl;

        fieldEl.getDOMNode().value = 'a'.repeat(maxLength + 1);
        fieldEl.simulate('input');

        const { counterEl, fieldComponent } = getElements(wrapper)[field];
        assert.isOk(counterIsInErrorState(counterEl));
        assert.isOk(componentIsInErrorState(fieldComponent));
      });
    });
  });

  describe('name field', () => {
    it("doesn't go into an error state when too few characters are only input but not committed", () => {
      const { wrapper, elements } = createWrapper();
      const fieldEl = elements.name.fieldEl;

      fieldEl.getDOMNode().value = 'aa';
      fieldEl.simulate('input');

      const { counterEl, fieldComponent } = getElements(wrapper).name;
      assert.isNotOk(counterIsInErrorState(counterEl));
      assert.isNotOk(componentIsInErrorState(fieldComponent));
    });

    it('goes into an error state when too few characters are committed', () => {
      const { wrapper, elements } = createWrapper();
      const fieldEl = elements.name.fieldEl;

      // Too few characters are entered into the field and the field is then
      // "committed" (e.g. the focus leaves the field, or the form is
      // submitted.)
      fieldEl.getDOMNode().value = 'aa';
      fieldEl.simulate('change');

      // The field and its character counter go into their error states.
      let { counterEl, fieldComponent } = getElements(wrapper).name;
      assert.isOk(counterIsInErrorState(counterEl));
      assert.isOk(componentIsInErrorState(fieldComponent));

      // If enough characters are then just input into the field (they don't
      // have to be committed) then the error state is already cleared.
      fieldEl.getDOMNode().value = 'aaa';
      fieldEl.simulate('input');
      ({ counterEl, fieldComponent } = getElements(wrapper).name);
      assert.isNotOk(counterIsInErrorState(counterEl));
      assert.isNotOk(componentIsInErrorState(fieldComponent));
    });
  });

  it("doesn't show an error message initially", async () => {
    const { wrapper } = createWrapper();

    assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
  });

  it("doesn't show a loading state initially", async () => {
    const { wrapper } = createWrapper();

    await assertInLoadingState(wrapper, false);
  });

  it('shows a loading state when the create-group API request is in-flight', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves(new Promise(() => {}));

    wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
  });

  it('continues to show the loading state after receiving a successful API response', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves({ links: { html: 'https://example.com/group/foo' } });

    await wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
  });

  it('creates the group and redirects the browser', async () => {
    const { wrapper, elements } = createWrapper();
    const nameEl = elements.name.fieldEl;
    const descriptionEl = elements.description.fieldEl;
    const groupURL = 'https://example.com/group/foo';
    fakeCallAPI.resolves({ links: { html: groupURL } });

    const name = 'Test Group Name';
    const description = 'Test description';
    nameEl.getDOMNode().value = name;
    nameEl.simulate('input');
    descriptionEl.getDOMNode().value = description;
    descriptionEl.simulate('input');
    await wrapper.find('form[data-testid="form"]').simulate('submit');

    assert.isTrue(
      fakeCallAPI.calledOnceWithExactly(
        config.api.createGroup.url,
        config.api.createGroup.method,
        {
          name,
          description,
        },
      ),
    );
    assert.isTrue(fakeSetLocation.calledOnceWithExactly(groupURL));
  });

  it('shows an error message if callAPI() throws an error', async () => {
    const errorMessageFromCallAPI = 'Bad API call.';
    fakeCallAPI.rejects({ message: errorMessageFromCallAPI });
    const { wrapper } = createWrapper();

    wrapper.find('form[data-testid="form"]').simulate('submit');

    const errorMessageEl = await waitForElement(
      wrapper,
      '[data-testid="error-message"]',
    );
    assert.equal(errorMessageEl.text(), errorMessageFromCallAPI);
    // It exits its loading state after receiving an error response.
    await assertInLoadingState(wrapper, false);
  });
});

async function assertInLoadingState(wrapper, inLoadingState) {
  await waitForElement(
    wrapper,
    `button[data-testid="button"][disabled=${inLoadingState}]`,
  );
  assert.equal(wrapper.exists('[data-testid="spinner"]'), inLoadingState);
}
