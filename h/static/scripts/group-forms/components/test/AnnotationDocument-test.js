import { mount } from '@hypothesis/frontend-testing';

import AnnotationDocument from '../AnnotationDocument';

describe('AnnotationDocument', () => {
  function createComponent(pageNumber) {
    const fakeAnnotation = {
      target: [
        {
          selector: [
            {
              type: 'PageSelector',
              label: pageNumber,
            },
          ],
        },
      ],
    };
    return mount(<AnnotationDocument annotation={fakeAnnotation} />);
  }

  it('does not show page number it does not exist in annotation', () => {
    const wrapper = createComponent();

    assert.isFalse(wrapper.exists('[data-testid="comma-wrapper"]'));
    assert.isFalse(wrapper.exists('[data-testid="page-number"]'));
  });

  ['15', '100', '1'].forEach(pageNumber => {
    it('shows page number and comma if page number exists in annotation', () => {
      const wrapper = createComponent(pageNumber);

      assert.isTrue(wrapper.exists('[data-testid="comma-wrapper"]'));

      const pageNumberEl = wrapper.find('[data-testid="page-number"]');
      assert.isTrue(pageNumberEl.exists());
      assert.equal(pageNumberEl.text(), `p. ${pageNumber}`);
    });
  });
});
