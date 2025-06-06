import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import AnnotationUser from '../AnnotationUser';

describe('AnnotationUser', () => {
  const createAnnotationUser = props => {
    return mount(<AnnotationUser displayName="Filbert Bronzo" {...props} />);
  };

  it('links to the author activity page if link provided', () => {
    const wrapper = createAnnotationUser({
      authorLink: 'http://www.foo.bar/baz',
    });

    assert.isTrue(wrapper.find('a[href="http://www.foo.bar/baz"]').exists());
  });

  it('does not link to the author activity page if no link provided', () => {
    const wrapper = createAnnotationUser();

    assert.isFalse(wrapper.find('a').exists());
  });

  it('renders the author name', () => {
    const wrapper = createAnnotationUser();

    assert.equal(wrapper.text(), 'Filbert Bronzo');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createAnnotationUser(),
    }),
  );
});
