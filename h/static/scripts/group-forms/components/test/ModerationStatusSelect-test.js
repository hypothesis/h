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

  function createComponent(props = {}) {
    return mount(
      <ModerationStatusSelect onChange={fakeOnChange} {...props} />,
      { connected: true },
    );
  }

  [
    { selected: undefined, expectedText: 'All' },
    { selected: 'PENDING', expectedText: 'Pending' },
    { selected: 'APPROVED', expectedText: 'Approved' },
    { selected: 'DENIED', expectedText: 'Denied' },
    { selected: 'SPAM', expectedText: 'Spam' },
  ].forEach(({ selected, expectedText }) => {
    it('shows selected option as button content', () => {
      const wrapper = createComponent({ selected });
      assert.equal(wrapper.text(), expectedText);
    });

    it('calls onChange when changing selected item', () => {
      const wrapper = createComponent();

      assert.notCalled(fakeOnChange);
      wrapper.find('Select').props().onChange(selected);
      assert.calledWith(fakeOnChange, selected);
    });
  });

  const commonOptions = ['Pending', 'Approved', 'Denied', 'Spam'];

  [
    { mode: 'filter', expectedOptions: ['All', ...commonOptions] },
    { mode: 'select', expectedOptions: commonOptions },
  ].forEach(({ mode, expectedOptions }) => {
    it('shows expected list of options', async () => {
      const wrapper = createComponent({ mode });

      // Open listbox
      wrapper.find('button').simulate('click');
      const options = await waitForElement(wrapper, '[role="option"]');

      assert.lengthOf(options, expectedOptions.length);
      expectedOptions.forEach((option, index) => {
        assert.equal(options.at(index).text(), option);
      });
    });
  });

  [
    { mode: 'filter', expectedIcon: 'FilterIcon' },
    { mode: 'select', selected: 'PENDING', expectedIcon: 'DottedCircleIcon' },
    { mode: 'select', selected: 'APPROVED', expectedIcon: 'CheckAllIcon' },
    { mode: 'select', selected: 'DENIED', expectedIcon: 'RestrictedIcon' },
    { mode: 'select', selected: 'SPAM', expectedIcon: 'CautionIcon' },
  ].forEach(({ mode, selected, expectedIcon }) => {
    it('shows expected icon in toggle button', () => {
      const wrapper = createComponent({ mode, selected });
      assert.isTrue(wrapper.exists(expectedIcon));
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
