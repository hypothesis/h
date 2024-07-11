import { mount } from 'enzyme';

import CreateGroupForm from '../CreateGroupForm';

describe('CreateGroupForm', () => {
  const createWrapper = () => mount(<CreateGroupForm />);

  [
    { counter: 'name', limit: 25 },
    { counter: 'description', limit: 250 },
  ].forEach(({ counter, limit }) => {
    describe(`${counter} character counter`, () => {
      it(`initially renders 0/${limit}`, () => {
        const wrapper = createWrapper();
        const counterEl = wrapper.find(
          `[data-testid="character-counter-${counter}"]`,
        );

        assert.equal(counterEl.text(), `0/${limit}`);
      });
    });
  });
});
