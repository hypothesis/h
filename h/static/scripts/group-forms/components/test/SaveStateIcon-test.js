import { mount } from 'enzyme';
import SaveStateIcon from '../SaveStateIcon';

describe('SaveStateIcon', () => {
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
      const wrapper = mount(<SaveStateIcon state={state} />);
      assert.equal(wrapper.exists('CheckIcon'), checkIcon);
      assert.equal(wrapper.exists('SpinnerSpokesIcon'), spinnerIcon);
    });
  });
});
