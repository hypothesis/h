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
    return component.prop('error') !== undefined;
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
      limit: 25,
    },
    {
      field: 'description',
      limit: 250,
    },
  ].forEach(({ field, limit }) => {
    describe(`${field} character counter`, () => {
      it('renders a character counter', () => {
        const { counterEl, fieldComponent } = createWrapper().elements[field];

        assert.equal(counterEl.text(), `0/${limit}`);
        assert.isNotOk(counterIsInErrorState(counterEl));
        assert.isNotOk(componentIsInErrorState(fieldComponent));
      });

      it("changes the count when the field's text changes", () => {
        const { wrapper, elements } = createWrapper();
        const fieldEl = elements[field].fieldEl;

        fieldEl.getDOMNode().value = 'new text';
        fieldEl.simulate('input');

        const { counterEl, fieldComponent } = getElements(wrapper)[field];
        assert.equal(counterEl.text(), `8/${limit}`);
        assert.isNotOk(counterIsInErrorState(counterEl));
        assert.isNotOk(componentIsInErrorState(fieldComponent));
      });

      it('goes into an error state when too many characters are entered', () => {
        const { wrapper, elements } = createWrapper();
        const fieldEl = elements[field].fieldEl;

        fieldEl.getDOMNode().value = 'a'.repeat(limit + 1);
        fieldEl.simulate('input');

        const { counterEl, fieldComponent } = getElements(wrapper)[field];
        assert.isOk(counterIsInErrorState(counterEl));
        assert.isOk(componentIsInErrorState(fieldComponent));
      });
    });
  });

  it("doesn't show an error message initially", async () => {
    const { wrapper } = createWrapper();

    assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
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
  });
});
