import { mount } from 'enzyme';

import TextField from '../TextField';

function unicodeLen(value) {
  return [...value].length;
}

describe('TextField', () => {
  [
    {
      value: '',
      minLength: 0,
      maxLength: 10,
      error: null,
    },
    {
      value: 'abc',
      minLength: 0,
      maxLength: 10,
      error: null,
    },
    // Too few characters
    {
      value: 'a',
      minLength: 2,
      maxLength: 10,
      error: 'Must be 2 characters or more.',
    },
    // Too many characters
    {
      value: 'abc',
      minLength: 0,
      maxLength: 2,
      error: 'Must be 2 characters or less.',
    },
  ].forEach(({ value, minLength, maxLength, error }) => {
    it('displays character count and sets field error', () => {
      const wrapper = mount(
        <TextField
          type="input"
          value={value}
          minLength={minLength}
          maxLength={maxLength}
          testid="field"
        />,
      );

      // The "too few characters" message is not shown until a change has
      // been committed in the field.
      wrapper.find('input').simulate('change');

      const expectError = error !== null;

      const count = wrapper.find('[data-testid="charcounter-field"]');
      const expectedText = `${unicodeLen(value)}/${maxLength}`;
      assert.equal(count.text(), expectedText);
      assert.equal(count.hasClass('text-red-error'), expectError);
      assert.equal(wrapper.find('Input').prop('error'), error ?? '');
    });
  });

  it('invokes callback when text is entered', () => {
    const onChange = sinon.stub();
    const wrapper = mount(
      <TextField type="input" value="" onChangeValue={onChange} />,
    );

    wrapper.find('input').getDOMNode().value = 'foo';
    wrapper.find('input').simulate('input');

    assert.calledWith(onChange, 'foo');
  });
});
