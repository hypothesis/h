import {
  checkAccessibility,
  mount,
  waitForElement,
} from '@hypothesis/frontend-testing';

import ModerationStatusSelect from '../ModerationStatusSelect';

describe('ModerationStatusSelect', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(selected) {
    return mount(
      <ModerationStatusSelect selected={selected} onChange={fakeOnChange} />,
      { connected: true },
    );
  }

  [
    { selected: undefined, expectedText: 'All' },
    { selected: 'pending', expectedText: 'Pending' },
    { selected: 'approved', expectedText: 'Approved' },
    { selected: 'denied', expectedText: 'Denied' },
    { selected: 'spam', expectedText: 'Spam' },
  ].forEach(({ selected, expectedText }) => {
    it('shows selected option as button content', () => {
      const wrapper = createComponent(selected);
      assert.equal(wrapper.text(), expectedText);
    });

    it('calls onChange when changing selected item', () => {
      const wrapper = createComponent();

      assert.notCalled(fakeOnChange);
      wrapper.find('Select').props().onChange(selected);
      assert.calledWith(fakeOnChange, selected);
    });
  });

  it('shows expected list of options', async () => {
    const wrapper = createComponent();

    // Open listbox
    wrapper.find('button').simulate('click');
    const options = await waitForElement(wrapper, '[role="option"]');

    assert.lengthOf(options, 5);
    assert.equal(options.at(0).text(), 'All');
    assert.equal(options.at(1).text(), 'Pending');
    assert.equal(options.at(2).text(), 'Approved');
    assert.equal(options.at(3).text(), 'Denied');
    assert.equal(options.at(4).text(), 'Spam');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
