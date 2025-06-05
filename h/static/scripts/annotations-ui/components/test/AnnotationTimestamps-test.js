import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import AnnotationTimestamps, { $imports } from '../AnnotationTimestamps';

describe('AnnotationTimestamps', () => {
  let clock;
  let fakeFormatDateTime;
  let fakeFormatRelativeDate;
  let fakeDecayingInterval;

  const createComponent = props =>
    mount(
      <AnnotationTimestamps
        annotationCreated="2015-05-10T20:18:56.613388+00:00"
        annotationUpdated="2015-05-10T20:18:56.613388+00:00"
        annotationURL="http://www.example.com"
        withEditedTimestamp={false}
        {...props}
      />,
    );

  beforeEach(() => {
    clock = sinon.useFakeTimers();
    fakeFormatDateTime = sinon.stub().returns('absolute date');
    fakeFormatRelativeDate = sinon.stub().returns('fuzzy string');
    fakeDecayingInterval = sinon.stub();

    $imports.$mock({
      '@hypothesis/frontend-shared': {
        formatDateTime: fakeFormatDateTime,
        formatRelativeDate: fakeFormatRelativeDate,
        decayingInterval: fakeDecayingInterval,
      },
    });
  });

  afterEach(() => {
    clock.restore();
    $imports.$restore();
  });

  it('renders a linked created timestamp if annotation has a link', () => {
    const wrapper = createComponent();

    const link = wrapper.find('a');
    assert.equal(link.prop('href'), 'http://www.example.com');
    assert.equal(link.prop('title'), 'absolute date');
    assert.equal(link.text(), 'fuzzy string');
  });

  it('renders an unlinked created timestamp if annotation does not have a link', () => {
    const wrapper = createComponent({ annotationURL: '' });

    const link = wrapper.find('Link');
    const span = wrapper.find('span[data-testid="timestamp-created"]');
    assert.isFalse(link.exists());
    assert.isTrue(span.exists());
    assert.equal(span.text(), 'fuzzy string');
  });

  it('renders edited timestamp if `withEditedTimestamp` is true', () => {
    fakeFormatRelativeDate.onCall(1).returns('another fuzzy string');

    const wrapper = createComponent({ withEditedTimestamp: true });

    const editedTimestamp = wrapper.find('[data-testid="timestamp-edited"]');
    assert.isTrue(editedTimestamp.exists());
    assert.include(editedTimestamp.text(), '(edited another fuzzy string)');
  });

  it('does not render edited relative date if equivalent to created relative date', () => {
    fakeFormatRelativeDate.returns('equivalent fuzzy strings');

    const wrapper = createComponent({ withEditedTimestamp: true });

    const editedTimestamp = wrapper.find('[data-testid="timestamp-edited"]');
    assert.isTrue(editedTimestamp.exists());
    assert.include(editedTimestamp.text(), '(edited)');
  });

  it('is updated after time passes', () => {
    fakeDecayingInterval.callsFake((date, callback) => {
      const id = setTimeout(callback, 10);
      return () => clearTimeout(id);
    });
    const wrapper = createComponent();
    fakeFormatRelativeDate.returns('60 jiffies');

    act(() => {
      clock.tick(1000);
    });
    wrapper.update();

    assert.equal(wrapper.text(), '60 jiffies');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => {
        // Fake timers break axe-core.
        clock.restore();

        return createComponent();
      },
    }),
  );
});
