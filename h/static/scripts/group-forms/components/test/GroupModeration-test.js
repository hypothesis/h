import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import GroupModeration, { $imports } from '../GroupModeration';

describe('GroupModeration', () => {
  let fakeUseGroupAnnotations;

  beforeEach(() => {
    fakeUseGroupAnnotations = sinon.stub().returns({ loading: true });

    $imports.$mock({
      '../hooks/use-group-annotations': {
        useGroupAnnotations: fakeUseGroupAnnotations,
      },
    });
  });

  function createComponent(groupName = 'The group') {
    return mount(<GroupModeration group={{ name: groupName }} />);
  }

  it('renders form header', () => {
    const wrapper = createComponent();
    assert.equal(
      wrapper.find('GroupFormHeader').prop('title'),
      'Moderate group',
    );
  });

  describe('moderation status filter', () => {
    it('shows pending status initially', () => {
      const wrapper = createComponent();
      assert.equal(
        wrapper.find('ModerationStatusSelect').prop('selected'),
        'PENDING',
      );
    });

    ['APPROVED', 'DENIED', 'SPAM'].forEach(newStatus => {
      it('changes selected status on ModerationStatusSelect change', () => {
        const wrapper = createComponent();

        wrapper.find('ModerationStatusSelect').props().onChange(newStatus);
        wrapper.update();

        assert.equal(
          wrapper.find('ModerationStatusSelect').prop('selected'),
          newStatus,
        );
      });
    });
  });

  describe('annotations list', () => {
    [true, false].forEach(loading => {
      it('shows loading indicator when loading', () => {
        fakeUseGroupAnnotations.returns({ loading, annotations: [] });
        const wrapper = createComponent();

        assert.equal(wrapper.exists('Spinner'), loading);
      });
    });

    [
      { status: 'PENDING', expectedFallbackMessage: 'You are all set!' },
      {
        status: 'APPROVED',
        expectedFallbackMessage: 'No annotations found for selected status',
      },
      {
        status: 'DENIED',
        expectedFallbackMessage: 'No annotations found for selected status',
      },
      {
        status: 'SPAM',
        expectedFallbackMessage: 'No annotations found for selected status',
      },
    ].forEach(({ status, expectedFallbackMessage }) => {
      it('shows fallback message when no annotations exist', () => {
        fakeUseGroupAnnotations.returns({ loading: false, annotations: [] });
        const wrapper = createComponent();

        wrapper.find('ModerationStatusSelect').props().onChange(status);
        wrapper.update();

        assert.equal(
          wrapper.find('[data-testid="annotations-fallback-message"]').text(),
          expectedFallbackMessage,
        );
      });
    });

    it('renders every annotation that was loaded', () => {
      const annotations = [
        { id: '1', text: 'First annotation' },
        { id: '2', text: 'Second annotation' },
        { id: '3', text: 'Third annotation' },
      ];
      fakeUseGroupAnnotations.returns({ loading: false, annotations });

      const wrapper = createComponent();
      const annotationNodes = wrapper
        .find('AnnotationListContent')
        .find('article');

      assert.lengthOf(annotationNodes, annotations.length);
      annotations.forEach((anno, index) => {
        assert.equal(annotationNodes.at(index).text(), anno.text);
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
