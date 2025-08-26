import {
  checkAccessibility,
  mockImportedComponents,
  mount,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';

import { GroupFormsConfig } from '../../config';
import { APIError } from '../../util/api';
import AnnotationCard, { $imports } from '../AnnotationCard';

describe('AnnotationCard', () => {
  let fakeConfig;
  let fakeAnnotation;
  let fakeOnStatusChange;
  let fakeOnAnnotationReloaded;
  let fakeUseUpdateModerationStatus;
  let fakeCallAPI;

  beforeEach(() => {
    fakeConfig = {
      context: {},
      api: {
        annotationDetail: { url: '/api/annotations/:annotationId' },
      },
      routes: {
        'activity.user_search': 'https://example.com/users/:username',
      },
    };
    fakeAnnotation = {
      tags: [],
      links: {
        incontext: 'https://example.com',
      },
      target: [
        {
          selector: [
            {
              type: 'TextQuoteSelector',
              exact: 'The quote',
            },
          ],
        },
      ],
    };

    fakeOnStatusChange = sinon.stub();
    fakeOnAnnotationReloaded = sinon.stub();
    fakeUseUpdateModerationStatus = sinon.stub().returns(sinon.stub());
    fakeCallAPI = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '@hypothesis/annotation-ui': {
        AnnotationTimestamps: () => null,
        AnnotationUser: () => null,
        AnnotationGroupInfo: () => null,
        AnnotationShareControl: () => null,
      },
      '@hypothesis/frontend-shared': {
        lazy: displayName => {
          const DummyComponent = () => null;
          DummyComponent.displayName = displayName;
          return DummyComponent;
        },
      },
      '../hooks/use-update-moderation-status': {
        useUpdateModerationStatus: fakeUseUpdateModerationStatus,
      },
      '../util/api': {
        callAPI: fakeCallAPI,
      },
    });
  });

  function createComponent(props = {}) {
    return mount(
      <GroupFormsConfig.Provider value={fakeConfig}>
        <AnnotationCard
          annotation={fakeAnnotation}
          disableModeration={false}
          onStatusChange={fakeOnStatusChange}
          onAnnotationReloaded={fakeOnAnnotationReloaded}
          {...props}
        />
      </GroupFormsConfig.Provider>,
    );
  }

  [
    {
      userInfo: undefined,
      annotationUser: 'acct:foo@example.com',
      expectedDisplayName: 'foo',
      expectedLink: 'https://example.com/users/foo',
    },
    {
      userInfo: {
        display_name: 'Jane Doe',
      },
      annotationUser: 'acct:foo@example.com',
      expectedDisplayName: 'Jane Doe',
      expectedLink: 'https://example.com/users/foo',
    },
    {
      userInfo: undefined,
      annotationUser: 'invalid',
      expectedDisplayName: 'invalid',
      expectedLink: undefined,
    },
  ].forEach(
    ({ userInfo, annotationUser, expectedDisplayName, expectedLink }) => {
      it('renders expected username and profile link', () => {
        fakeAnnotation.user_info = userInfo;
        fakeAnnotation.user = annotationUser;

        const wrapper = createComponent();

        const userHeader = wrapper.find('AnnotationUser');
        assert.equal(userHeader.prop('displayName'), expectedDisplayName);
        assert.equal(userHeader.prop('authorLink'), expectedLink);
      });
    },
  );

  [
    { group: null, shouldRenderGroupInfo: false },
    {
      group: { type: '', name: '', link: '' },
      shouldRenderGroupInfo: true,
    },
  ].forEach(({ group, shouldRenderGroupInfo }) => {
    it('renders AnnotationGroupInfo if a group exists in the config', () => {
      fakeConfig.context.group = group;
      const wrapper = createComponent();

      assert.equal(
        wrapper.exists('AnnotationGroupInfo'),
        shouldRenderGroupInfo,
      );
    });
  });

  [
    { created: '2025-01-01', updated: '2025-01-01' },
    { created: '2025-01-01', updated: '2025-01-05' },
  ].forEach(({ created, updated }) => {
    it('renders annotation dates in AnnotationTimestamps', () => {
      fakeAnnotation.created = created;
      fakeAnnotation.updated = updated;

      const wrapper = createComponent();
      const timestamps = wrapper.find('AnnotationTimestamps');

      assert.equal(
        timestamps.prop('annotationCreated'),
        fakeAnnotation.created,
      );
      assert.equal(
        timestamps.prop('annotationUpdated'),
        fakeAnnotation.updated,
      );
      assert.equal(
        timestamps.prop('withEditedTimestamp'),
        fakeAnnotation.created !== fakeAnnotation.updated ? 'prominent' : false,
      );
    });
  });

  [{ tags: [] }, { tags: ['foo', 'bar', 'baz'] }].forEach(({ tags }) => {
    it('renders annotation tags when present', () => {
      fakeAnnotation.tags = tags;

      const wrapper = createComponent();
      const tagsContainer = wrapper.find('[data-testid="tags-container"]');
      const hasTags = tags.length > 0;

      assert.equal(tagsContainer.exists(), hasTags);
      if (hasTags) {
        assert.lengthOf(tagsContainer.find('li'), tags.length);
      }
    });
  });

  it('has a link to the annotation in context', () => {
    fakeAnnotation.links.incontext = 'https://example.com';
    const wrapper = createComponent();

    assert.equal(
      wrapper.find('a[data-testid="context-link"]').prop('href'),
      fakeAnnotation.links.incontext,
    );
  });

  it('extracts the annotation quote', () => {
    const wrapper = createComponent();
    assert.equal(wrapper.find('blockquote').text(), 'The quote');
  });

  it('does not render quote elements for quoteless annotations', () => {
    fakeAnnotation.target[0].selector = [];
    const wrapper = createComponent();

    assert.isFalse(wrapper.exists('blockquote'));
  });

  ['PENDING', 'APPROVED', 'DENIED', 'SPAM'].forEach(status => {
    it("renders ModerationStatusSelect with annotation's status", () => {
      fakeAnnotation.moderation_status = status;
      const wrapper = createComponent();

      assert.equal(
        wrapper.find('ModerationStatusSelect').prop('selected'),
        status,
      );
    });

    it('changes moderation status when ModerationStatusSelect.onChange is called', async () => {
      const fakeUpdateModerationStatus = sinon.stub();
      fakeUseUpdateModerationStatus.returns(fakeUpdateModerationStatus);

      const wrapper = createComponent();
      await wrapper.find('ModerationStatusSelect').props().onChange(status);

      assert.calledWith(fakeUpdateModerationStatus, status);

      assert.calledWith(fakeOnStatusChange.firstCall, { saveState: 'saving' });
      assert.calledWith(fakeOnStatusChange.secondCall, {
        saveState: 'saved',
        newModerationStatus: status,
      });
    });
  });

  it('disables ModerationStatusSelect while updating moderation status', async () => {
    const { promise, resolve } = Promise.withResolvers();
    fakeUseUpdateModerationStatus.returns(sinon.stub().returns(promise));
    const wrapper = createComponent();

    assert.isFalse(wrapper.find('ModerationStatusSelect').prop('disabled'));
    wrapper.find('ModerationStatusSelect').props().onChange('APPROVED');
    wrapper.update();
    assert.isTrue(wrapper.find('ModerationStatusSelect').prop('disabled'));

    resolve(undefined);
    await promise;
  });

  [true, false].forEach(disableModeration => {
    it('disables ModerationStatusSelect while disableModeration is `true`', () => {
      const wrapper = createComponent({ disableModeration });
      assert.equal(
        wrapper.find('ModerationStatusSelect').prop('disabled'),
        disableModeration,
      );
    });
  });

  [
    {
      error: new Error(''),
      expectedMessage: 'An error occurred updating the moderation status.',
      errorElementId: 'update-error',
    },
    {
      error: new APIError('', {
        response: new Response(null, { status: 409 }),
      }),
      callAPIShouldFail: false,
      expectedMessage:
        'The annotation has been updated since this page was loaded. Review this new version and try again.',
      errorElementId: 'update-warning',
    },
    {
      error: new APIError('', {
        response: new Response(null, { status: 409 }),
      }),
      callAPIShouldFail: true,
      expectedMessage:
        'The annotation has been updated since this page was loaded.',
      errorElementId: 'update-error',
    },
  ].forEach(({ error, callAPIShouldFail, expectedMessage, errorElementId }) => {
    it('shows errors produced while changing status', async () => {
      fakeUseUpdateModerationStatus.returns(sinon.stub().throws(error));
      if (callAPIShouldFail) {
        fakeCallAPI.rejects(new Error(''));
      }

      const wrapper = createComponent();

      wrapper.find('ModerationStatusSelect').props().onChange('APPROVED');
      wrapper.update();

      const errorElement = await waitForElement(
        wrapper,
        `Callout[data-testid="${errorElementId}"]`,
      );
      assert.equal(errorElement.text(), expectedMessage);
    });
  });

  it('reloads annotation when a conflict occurs while changing status', async () => {
    const newAnnotationData = { text: 'New annotation' };
    fakeCallAPI.resolves(newAnnotationData);
    fakeUseUpdateModerationStatus.returns(
      sinon.stub().throws(
        new APIError('', {
          response: new Response(null, { status: 409 }),
        }),
      ),
    );

    const wrapper = createComponent();
    wrapper.find('ModerationStatusSelect').props().onChange('APPROVED');

    await waitFor(() => fakeOnAnnotationReloaded.calledWith(newAnnotationData));
  });

  [
    { references: undefined, showsReplyIndicator: false },
    { references: [], showsReplyIndicator: false },
    { references: ['1', '2'], showsReplyIndicator: true },
  ].forEach(({ references, showsReplyIndicator }) => {
    it('adds reply indicator for annotations that are replies', () => {
      fakeAnnotation.references = references;
      const wrapper = createComponent();

      assert.equal(
        wrapper.exists('[data-testid="reply-indicator"]'),
        showsReplyIndicator,
      );
    });
  });

  context('when annotation body is collapsible', () => {
    it('shows an excerpt toggle button', () => {
      const wrapper = createComponent();
      const getBodyExcerpt = () =>
        wrapper.find('Excerpt[data-testid="anno-body-excerpt"]');
      const getToggleButton = () =>
        wrapper.find('button[data-testid="toggle-anno-body"]');

      getBodyExcerpt().props().onCollapsibleChanged(true);
      wrapper.update();

      const toggleButton = getToggleButton();
      assert.isTrue(toggleButton.exists());
      assert.equal(toggleButton.text(), 'Show more');
      assert.isTrue(getBodyExcerpt().prop('collapsed'));

      toggleButton.simulate('click');

      assert.isFalse(getBodyExcerpt().prop('collapsed'));
      assert.equal(getToggleButton().text(), 'Show less');
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
