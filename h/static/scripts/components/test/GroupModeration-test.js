import {
  checkAccessibility,
  mount,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';

import GroupModeration, { $imports } from '../GroupModeration';

describe('GroupModeration', () => {
  let fakeUseGroupAnnotations;
  let fakeLoadNextPage;
  let fakeUpdateAnnotationStatus;
  let fakeUpdateAnnotation;

  beforeEach(() => {
    fakeLoadNextPage = sinon.stub();
    fakeUpdateAnnotationStatus = sinon.stub();
    fakeUpdateAnnotation = sinon.stub();
    fakeUseGroupAnnotations = sinon.stub().returns({
      loading: true,
      removedAnnotations: new Set(),
      loadNextPage: fakeLoadNextPage,
      updateAnnotationStatus: fakeUpdateAnnotationStatus,
      updateAnnotation: fakeUpdateAnnotation,
    });

    $imports.$mock(mockImportedComponents());
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
    [
      { queryParamStatus: undefined, expectedSelectedStatus: 'PENDING' },
      { queryParamStatus: 'invalid', expectedSelectedStatus: 'PENDING' },
      { queryParamStatus: 'ALL', expectedSelectedStatus: undefined },
      { queryParamStatus: 'APPROVED', expectedSelectedStatus: 'APPROVED' },
      { queryParamStatus: 'DENIED', expectedSelectedStatus: 'DENIED' },
      { queryParamStatus: 'SPAM', expectedSelectedStatus: 'SPAM' },
      { queryParamStatus: 'PENDING', expectedSelectedStatus: 'PENDING' },
    ].forEach(({ queryParamStatus, expectedSelectedStatus }) => {
      it('shows expected initial status', () => {
        if (queryParamStatus) {
          history.replaceState(
            null,
            '',
            `?moderation_status=${queryParamStatus}`,
          );
        }

        const wrapper = createComponent();

        assert.equal(
          wrapper.find('ModerationStatusSelect').prop('selected'),
          expectedSelectedStatus,
        );
      });
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
        assert.equal(location.search, `?moderation_status=${newStatus}`);
      });
    });
  });

  describe('annotations list', () => {
    [true, false].forEach(loading => {
      it('shows loading indicator when loading', () => {
        fakeUseGroupAnnotations.returns({ loading });
        const wrapper = createComponent();

        assert.equal(wrapper.exists('Spinner'), loading);
      });
    });

    [
      {
        status: undefined,
        expectedFallbackMessage: 'There are no annotations in this group.',
      },
      {
        status: 'PENDING',
        expectedFallbackMessage:
          'There are no Pending annotations in this group.',
      },
      {
        status: 'APPROVED',
        expectedFallbackMessage:
          'There are no Approved annotations in this group.',
      },
      {
        status: 'DENIED',
        expectedFallbackMessage:
          'There are no Declined annotations in this group.',
      },
      {
        status: 'SPAM',
        expectedFallbackMessage: 'There are no Spam annotations in this group.',
      },
    ].forEach(({ status, expectedFallbackMessage }) => {
      it('shows fallback message when no visible annotations exist', () => {
        fakeUseGroupAnnotations.returns({
          loading: false,
          annotations: [],
          visibleAnnotations: 0,
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
      fakeUseGroupAnnotations.returns({
        loading: false,
        annotations,
        removedAnnotations: new Set(),
      });

      const wrapper = createComponent();
      const annotationNodes = wrapper
        .find('AnnotationListContent')
        .find('AnnotationCard');

      assert.lengthOf(annotationNodes, annotations.length);
      annotations.forEach((anno, index) => {
        assert.equal(annotationNodes.at(index).prop('annotation'), anno);
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

    ['PENDING', 'APPROVED', 'DENIED', 'SPAM'].forEach(newModerationStatus => {
      it('calls updateAnnotationStatus when onStatusChange is called', () => {
        const annotations = [
          { id: '1', text: 'First annotation' },
          { id: '2', text: 'Second annotation' },
        ];
        fakeUseGroupAnnotations.returns({
          loading: false,
          annotations,
          updateAnnotationStatus: fakeUpdateAnnotationStatus,
          removedAnnotations: new Set(),
        });

        const wrapper = createComponent();
        const annotationNodes = wrapper.find('AnnotationCard');

        annotations.forEach((anno, index) => {
          annotationNodes
            .at(index)
            .props()
            .onStatusChange({ saveState: 'saved', newModerationStatus });
          assert.calledWith(
            fakeUpdateAnnotationStatus.lastCall,
            anno.id,
            newModerationStatus,
          );
        });
      });
    });

    it('sets `disableModeration` prop for all annotations when one is being moderated', () => {
      const annotations = [
        { id: '1', text: 'First annotation' },
        { id: '2', text: 'Second annotation' },
      ];
      fakeUseGroupAnnotations.returns({
        loading: false,
        annotations,
        updateAnnotationStatus: fakeUpdateAnnotationStatus,
        removedAnnotations: new Set(),
      });

      const wrapper = createComponent();
      const annotationNodes = () => wrapper.find('AnnotationCard');

      annotationNodes().first().props().onStatusChange({ saveState: 'saving' });
      wrapper.update();

      annotationNodes().forEach(anno => {
        assert.isTrue(anno.prop('disableModeration'));
      });
    });

    it('calls updateAnnotation when onAnnotationReloaded is called', () => {
      const annotations = [
        { id: '1', text: 'First annotation' },
        { id: '2', text: 'Second annotation' },
      ];
      fakeUseGroupAnnotations.returns({
        loading: false,
        annotations,
        removedAnnotations: new Set(),
        updateAnnotation: fakeUpdateAnnotation,
      });

      const wrapper = createComponent();
      const annotationNodes = wrapper.find('AnnotationCard');

      annotations.forEach((anno, index) => {
        annotationNodes
          .at(index)
          .props()
          .onAnnotationReloaded({ text: 'updated annotation' });
        assert.calledWith(fakeUpdateAnnotation.lastCall, anno.id, {
          text: 'updated annotation',
        });
      });
    });

    it('wraps annotations in Slider components to animate removal', () => {
      const annotations = [
        { id: '1', text: 'First annotation' },
        { id: '2', text: 'Second annotation' },
      ];
      const removedAnnotations = new Set(['2']);
      fakeUseGroupAnnotations.returns({
        loading: false,
        annotations,
        removedAnnotations,
        updateAnnotationStatus: fakeUpdateAnnotationStatus,
      });

      const wrapper = createComponent();
      const sliders = wrapper.find('Slider');

      assert.lengthOf(sliders, annotations.length);

      // First annotation should have 'in' direction (not removed)
      assert.equal(sliders.at(0).prop('direction'), 'in');
      assert.equal(sliders.at(0).prop('delay'), '0.5s');

      // Second annotation should have 'out' direction (removed)
      assert.equal(sliders.at(1).prop('direction'), 'out');
      assert.equal(sliders.at(1).prop('delay'), '0.5s');
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
