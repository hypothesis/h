import { mount } from '@hypothesis/frontend-testing';

import { useFormValue } from '../form-value';

describe('useFormValue', () => {
  let lastValue;
  function TestWidget({ initial, opts }) {
    lastValue = useFormValue(initial, opts);
    return <div />;
  }

  it('returns initial value', () => {
    mount(<TestWidget initial="foo" />);
    assert.equal(lastValue.value, 'foo');
    assert.isUndefined(lastValue.error);
    assert.isFalse(lastValue.changed);
  });

  it('returns new value after update', () => {
    const wrapper = mount(<TestWidget initial="foo" />);

    lastValue.update('new-value');
    wrapper.update(); // Flush render

    assert.equal(lastValue.value, 'new-value');
    assert.isUndefined(lastValue.error);
    assert.isTrue(lastValue.changed);
  });

  it('returns new value after commit', () => {
    const wrapper = mount(<TestWidget initial="foo" />);

    lastValue.commit('new-value');
    wrapper.update(); // Flush render

    assert.equal(lastValue.value, 'new-value');
    assert.isUndefined(lastValue.error);
    assert.isTrue(lastValue.changed);
  });

  it('updates committed state', () => {
    const validate = sinon.stub();
    const opts = { validate };
    const wrapper = mount(<TestWidget initial="foo" opts={opts} />);
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
      initialError: 'Server error',
      validate: value => (value === 'invalid' ? 'Client error' : undefined),
    };
    const wrapper = mount(<TestWidget initial="foo" opts={opts} />);
    assert.equal(lastValue.error, 'Server error');

    lastValue.update('invalid');
    wrapper.update(); // Flush render
    assert.equal(lastValue.error, 'Client error');

    lastValue.update('valid');
    wrapper.update(); // Flush render
    assert.isUndefined(lastValue.error);
  });
});
