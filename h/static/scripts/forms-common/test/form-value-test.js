import { mount } from '@hypothesis/frontend-testing';

import { useFormValue } from '../form-value';

describe('useFormValue', () => {
  let lastValue;

  const form = {
    data: { text_field: 'foo' },
  };

  const formWithError = {
    ...form,
    errors: {
      text_field: 'Server error',
    },
  };

  function TestWidget({ form, field, defaultValue = '', opts = {} }) {
    lastValue = useFormValue(form, field, defaultValue, opts);
    return <div />;
  }

  it('returns initial value', () => {
    mount(<TestWidget form={form} field="text_field" />);
    assert.equal(lastValue.value, 'foo');
    assert.isUndefined(lastValue.error);
    assert.isFalse(lastValue.changed);
  });

  it('returns new value after update', () => {
    const wrapper = mount(<TestWidget form={form} field="text_field" />);

    lastValue.update('new-value');
    wrapper.update(); // Flush render

    assert.equal(lastValue.value, 'new-value');
    assert.isUndefined(lastValue.error);
    assert.isTrue(lastValue.changed);
  });

  it('returns new value after commit', () => {
    const wrapper = mount(<TestWidget form={form} field="text_field" />);

    lastValue.commit('new-value');
    wrapper.update(); // Flush render

    assert.equal(lastValue.value, 'new-value');
    assert.isUndefined(lastValue.error);
    assert.isTrue(lastValue.changed);
  });

  it('updates committed state', () => {
    const validate = sinon.stub();
    const opts = { validate };
    const wrapper = mount(
      <TestWidget form={form} field="text_field" opts={opts} />,
    );
    assert.isTrue(lastValue.committed);

    lastValue.update('new-val');
    wrapper.update();
    assert.isFalse(lastValue.committed);
    assert.calledWith(validate, 'new-val', false);

    lastValue.commit('new-value');
    wrapper.update();
    assert.isTrue(lastValue.committed);
    assert.calledWith(validate, 'new-value', true);
  });

  it('returns form error', () => {
    const opts = {
      validate: value => (value === 'invalid' ? 'Client error' : undefined),
    };
    const wrapper = mount(
      <TestWidget form={formWithError} field="text_field" opts={opts} />,
    );
    assert.equal(lastValue.error, 'Server error');

    lastValue.update('invalid');
    wrapper.update(); // Flush render
    assert.equal(lastValue.error, 'Client error');

    lastValue.update('valid');
    wrapper.update(); // Flush render
    assert.isUndefined(lastValue.error);
  });
});
