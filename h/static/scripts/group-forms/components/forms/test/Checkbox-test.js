import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import Checkbox from '../Checkbox';

describe('Checkbox', () => {
  function createComponent(props = {}) {
    return mount(<Checkbox {...props}>Click me</Checkbox>);
  }

  ['This is the description', undefined].forEach(description => {
    it('shows description when provided', () => {
      const wrapper = createComponent({ description });
      assert.equal(
        wrapper.exists('[data-testid="description"]'),
        !!description,
      );
    });
  });

  function idFromTestId(wrapper, testId) {
    return wrapper.find(`[data-testid="${testId}"]`).prop('id');
  }

  [
    // No description
    {
      props: {},
      getExpectedDescribedBy: () => undefined,
    },
    // Description
    {
      props: { description: 'The description' },
      getExpectedDescribedBy: wrapper => idFromTestId(wrapper, 'description'),
    },
  ].forEach(({ props, getExpectedDescribedBy }) => {
    it('describes checkbox with description element', () => {
      const wrapper = createComponent(props);

      assert.equal(
        wrapper.find('input[type="checkbox"]').prop('aria-describedby'),
        getExpectedDescribedBy(wrapper),
      );
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: createComponent }),
  );
});
