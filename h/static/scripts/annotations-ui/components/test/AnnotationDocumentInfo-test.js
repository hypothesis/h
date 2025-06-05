import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import AnnotationDocumentInfo from '../AnnotationDocumentInfo';

describe('AnnotationDocumentInfo', () => {
  const createAnnotationDocumentInfo = props => {
    return mount(
      <AnnotationDocumentInfo
        domain="www.foo.bar"
        link="http://www.baz"
        title="Turtles"
        {...props}
      />,
    );
  };

  it('should render the document title', () => {
    const wrapper = createAnnotationDocumentInfo();

    assert.include(wrapper.text(), '"Turtles"');
  });

  it('links to document in new tab/window when link available', () => {
    const wrapper = createAnnotationDocumentInfo();
    const link = wrapper.find('a');

    assert.equal(link.prop('href'), 'http://www.baz');
    assert.equal(link.prop('target'), '_blank');
  });

  it('does not link to document when no link available', () => {});

  it('should render domain if available', () => {
    const wrapper = createAnnotationDocumentInfo({ link: '' });

    const link = wrapper.find('a');
    assert.include(wrapper.text(), '"Turtles"');
    assert.isFalse(link.exists());
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => {
        return createAnnotationDocumentInfo();
      },
    }),
  );
});
