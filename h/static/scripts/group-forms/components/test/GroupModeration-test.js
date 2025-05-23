import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import GroupModeration, { $imports } from '../GroupModeration';

describe('GroupModeration', () => {
  let fakeUseGroupAnnotations;
  let fakeLoadNextPage;

  beforeEach(() => {
    fakeLoadNextPage = sinon.stub();
    fakeUseGroupAnnotations = sinon.stub().returns({
      loadingFirstPage: true,
      loadNextPage: fakeLoadNextPage,
    });

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
    [true, false].forEach(loadingFirstPage => {
      it('shows loading spinner when loading first page', () => {
        fakeUseGroupAnnotations.returns({ loadingFirstPage, annotations: [] });
        const wrapper = createComponent();

        assert.equal(wrapper.exists('Spinner'), loadingFirstPage);
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
        fakeUseGroupAnnotations.returns({
          loadingFirstPage: false,
          annotations: [],
        });
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
      fakeUseGroupAnnotations.returns({ loadingFirstPage: false, annotations });

      const wrapper = createComponent();
      const annotationNodes = wrapper
        .find('AnnotationListContent')
        .find('article');

      assert.lengthOf(annotationNodes, annotations.length);
      annotations.forEach((anno, index) => {
        assert.equal(annotationNodes.at(index).text(), anno.text);
      });
    });

    [true, false].forEach(loading => {
      it('shows page loading indicator when loading any page but the first', () => {
        fakeUseGroupAnnotations.returns({
          loading,
          loadingFirstPage: false,
          annotations: [{ id: '1', text: 'Annotation' }],
        });

        const wrapper = createComponent();

        assert.equal(
          wrapper.exists('[data-testid="page-loading-indicator"]'),
          loading,
        );
      });
    });

    [
      {
        scrollTop: 0,
        shouldCallNextPage: false,
      },
      {
        scrollTop: 2000,
        shouldCallNextPage: true,
      },
    ].forEach(({ scrollTop, shouldCallNextPage }) => {
      it('loads next page when scrolling down', () => {
        createComponent();

        window.scrollY = scrollTop;
        window.dispatchEvent(new Event('scroll'));

        assert.equal(fakeLoadNextPage.called, shouldCallNextPage);
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
