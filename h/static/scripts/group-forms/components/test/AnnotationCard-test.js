import {
  checkAccessibility,
  mockImportedComponents,
  mount,
} from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import AnnotationCard, { $imports } from '../AnnotationCard';

describe('AnnotationCard', () => {
  let fakeConfig;
  let fakeAnnotation;
  let fakeOnStatusChange;
  let fakeUseUpdateModerationStatus;

  beforeEach(() => {
    fakeConfig = {
      context: {},
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
    fakeUseUpdateModerationStatus = sinon.stub().returns(sinon.stub());

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '@hypothesis/annotation-ui': {
        AnnotationTimestamps: () => null,
        AnnotationUser: () => null,
        AnnotationGroupInfo: () => null,
        MarkdownView: () => null,
        AnnotationShareControl: () => null,
      },
      '../hooks/use-update-moderation-status': {
        useUpdateModerationStatus: fakeUseUpdateModerationStatus,
      },
    });
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <AnnotationCard
          annotation={fakeAnnotation}
          onStatusChange={fakeOnStatusChange}
        />
      </Config.Provider>,
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
        fakeAnnotation.created !== fakeAnnotation.updated,
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

  it('extract the annotation quote', () => {
    const wrapper = createComponent();
    assert.equal(wrapper.find('blockquote').text(), 'The quote');
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
      assert.calledWith(fakeOnStatusChange, status);
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

  it('shows errors produced while changing status', () => {
    fakeUseUpdateModerationStatus.returns(sinon.stub().throws(new Error('')));
    const wrapper = createComponent();

    wrapper.find('ModerationStatusSelect').props().onChange('APPROVED');
    wrapper.update();

    assert.equal(
      wrapper.find('[data-testid="update-error"]').text(),
      'An error occurred updating the moderation status',
    );
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

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
