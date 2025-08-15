import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import SaveStateIcon from '../SaveStateIcon';

describe('SaveStateIcon', () => {
  function createComponent(state) {
    return mount(<SaveStateIcon state={state} />);
  }

  [
    {
      state: 'unsaved',
      checkIcon: false,
      spinnerIcon: false,
    },
    {
      state: 'saving',
      checkIcon: false,
      spinnerIcon: true,
    },
    {
      state: 'saved',
      checkIcon: true,
      spinnerIcon: false,
    },
  ].forEach(({ state, checkIcon, spinnerIcon }) => {
    it(`shows expected icons in "${state}" state`, () => {
      const wrapper = createComponent(state);
      assert.equal(wrapper.exists('CheckIcon'), checkIcon);
      assert.equal(wrapper.exists('SpinnerSpokesIcon'), spinnerIcon);
    });

    it(
      'should pass a11y checks',
      checkAccessibility({ content: () => createComponent(state) }),
    );
  });
});
