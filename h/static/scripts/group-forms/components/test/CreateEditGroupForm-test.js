import { mount } from 'enzyme';
import { delay, waitForElement } from '@hypothesis/frontend-testing';

import {
  $imports,
  default as CreateEditGroupForm,
} from '../CreateEditGroupForm';

let config;

describe('CreateEditGroupForm', () => {
  let fakeCallAPI;
  let fakeSetLocation;
  let fakeUseWarnOnPageUnload;

  function pageUnloadWarningActive() {
    return fakeUseWarnOnPageUnload.lastCall.args[0] === true;
  }

  beforeEach(() => {
    config = {
      api: {
        createGroup: {
          method: 'POST',
          url: 'https://example.com/api/groups',
        },
      },
      context: {
        group: null,
      },
    };

    fakeCallAPI = sinon.stub();
    fakeSetLocation = sinon.stub();
    fakeUseWarnOnPageUnload = sinon.stub();

    $imports.$mock({
      '@hypothesis/frontend-shared': {
        useWarnOnPageUnload: fakeUseWarnOnPageUnload,
      },
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
      header: {
        element: wrapper.find('[data-testid="header"]'),
      },
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
      submitButton: {
        component: wrapper.find('Button[data-testid="button"]'),
        element: wrapper.find('button[data-testid="button"]'),
      },
    };
  };

  let wrappers;

  const createWrapper = () => {
    const wrapper = mount(<CreateEditGroupForm />);
    wrappers.push(wrapper);
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  beforeEach(() => {
    wrappers = [];
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
  });

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

  it('displays a create-new-group form', async () => {
    const { wrapper, elements } = createWrapper();
    const headerEl = elements.header.element;
    const nameEl = elements.name.fieldEl;
    const descriptionEl = elements.description.fieldEl;
    const submitButtonEl = elements.submitButton.element;

    assert.equal(headerEl.text(), 'Create a new private group');
    assert.equal(nameEl.getDOMNode().value, '');
    assert.equal(descriptionEl.getDOMNode().value, '');
    assert.equal(submitButtonEl.text(), 'Create group');
    assert.isFalse(wrapper.exists('[data-testid="back-link"]'));
    assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
    await assertInLoadingState(wrapper, false);
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  it('shows a loading state when the create-group API request is in-flight', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves(new Promise(() => {}));

    wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  it('continues to show the loading state after receiving a successful API response', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves({ links: { html: 'https://example.com/group/foo' } });

    await wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
    assert.isFalse(savedConfirmationShowing(wrapper));
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
      fakeCallAPI.calledOnceWithExactly(config.api.createGroup.url, {
        method: config.api.createGroup.method,
        headers: config.api.createGroup.headers,
        json: {
          name,
          description,
        },
      }),
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
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  context('when editing an existing group', () => {
    beforeEach(() => {
      config.context.group = {
        pubid: 'testid',
        name: 'Test Name',
        description: 'Test group description',
        link: 'https://example.com/groups/testid',
      };
      config.api.updateGroup = {
        method: 'PATCH',
        url: 'https://example.com/api/group/foo',
      };
    });

    it('displays an edit-group form', async () => {
      const { wrapper, elements } = createWrapper();
      const headerEl = elements.header.element;
      const nameEl = elements.name.fieldEl;
      const descriptionEl = elements.description.fieldEl;
      const submitButtonEl = elements.submitButton.element;

      assert.equal(headerEl.text(), 'Edit group');
      assert.equal(nameEl.getDOMNode().value, config.context.group.name);
      assert.equal(
        descriptionEl.getDOMNode().value,
        config.context.group.description,
      );
      assert.equal(submitButtonEl.text(), 'Save changes');
      assert.isTrue(wrapper.exists('[data-testid="back-link"]'));
      assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
      await assertInLoadingState(wrapper, false);
      assert.isFalse(savedConfirmationShowing(wrapper));
    });

    it('warns when closing tab if there are unsaved changes', async () => {
      const { wrapper, elements } = createWrapper();
      assert.isFalse(pageUnloadWarningActive());

      elements.name.fieldEl.simulate('input');
      assert.isTrue(pageUnloadWarningActive());

      wrapper.find('form[data-testid="form"]').simulate('submit');
      // Warning should still be active in saving state.
      assert.isTrue(pageUnloadWarningActive());
      await waitForElement(wrapper, 'SaveStateIcon[state="saved"]');

      // Warning should be disabled once saved.
      assert.isFalse(pageUnloadWarningActive());

      // Warning should be re-enabled if we then edit the form again.
      elements.description.fieldEl.simulate('input');
      assert.isTrue(pageUnloadWarningActive());

      // Warning should remain active if form is edited while being saved.
      wrapper.find('form[data-testid="form"]').simulate('submit');
      elements.name.fieldEl.simulate('input');
      await delay(0);
      assert.isTrue(pageUnloadWarningActive());
    });

    it('updates the group', async () => {
      const { wrapper, elements } = createWrapper();
      const nameEl = elements.name.fieldEl;
      const descriptionEl = elements.description.fieldEl;

      const name = 'Edited Group Name';
      const description = 'Edited group description';
      nameEl.getDOMNode().value = name;
      nameEl.simulate('input');
      descriptionEl.getDOMNode().value = description;
      descriptionEl.simulate('input');
      await wrapper.find('form[data-testid="form"]').simulate('submit');

      assert.isTrue(
        fakeCallAPI.calledOnceWithExactly(config.api.updateGroup.url, {
          method: config.api.updateGroup.method,
          headers: config.api.updateGroup.headers,
          json: {
            id: config.context.group.pubid,
            name,
            description,
          },
        }),
      );
    });

    it('shows a loading state when the update-group API request is in-flight', async () => {
      const { wrapper } = createWrapper();
      fakeCallAPI.resolves(new Promise(() => {}));

      wrapper.find('form[data-testid="form"]').simulate('submit');

      await assertInLoadingState(wrapper, true);
    });

    it('shows a confirmation after receiving a successful API response', async () => {
      const { wrapper } = createWrapper();
      fakeCallAPI.resolves();

      await wrapper.find('form[data-testid="form"]').simulate('submit');

      await assertInLoadingState(wrapper, false);
      assert.isTrue(savedConfirmationShowing(wrapper));
    });

    it('shows an error message if callAPI() throws an error', async () => {
      const errorMessageFromCallAPI = 'Bad API call.';
      fakeCallAPI.rejects(new Error(errorMessageFromCallAPI));
      const { wrapper } = createWrapper();

      wrapper.find('form[data-testid="form"]').simulate('submit');

      const errorMessageEl = await waitForElement(
        wrapper,
        '[data-testid="error-message"]',
      );
      assert.equal(errorMessageEl.text(), errorMessageFromCallAPI);
      await assertInLoadingState(wrapper, false);
      assert.isFalse(savedConfirmationShowing(wrapper));
    });

    ['name', 'description'].forEach(field => {
      it('clears the confirmation if fields are edited again', async () => {
        const { wrapper, elements } = createWrapper();
        const fieldEl = elements[field].fieldEl;
        fakeCallAPI.resolves();
        await wrapper.find('form[data-testid="form"]').simulate('submit');

        fieldEl.getDOMNode().value = 'new text';
        fieldEl.simulate('input');

        await assertInLoadingState(wrapper, false);
        assert.isFalse(savedConfirmationShowing(wrapper));
      });
    });
  });
});

async function assertInLoadingState(wrapper, inLoadingState) {
  await waitForElement(
    wrapper,
    `button[data-testid="button"][disabled=${inLoadingState}]`,
  );
  const state = wrapper.find('SaveStateIcon').prop('state');
  if (inLoadingState) {
    assert.equal(state, 'saving');
  } else {
    assert.notEqual(state, 'saving');
  }
}

function savedConfirmationShowing(wrapper) {
  return wrapper.find('SaveStateIcon').prop('state') === 'saved';
}
