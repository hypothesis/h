import { mount } from 'enzyme';

import CreateGroupForm from '../CreateGroupForm';

describe('CreateGroupForm', () => {
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
});
