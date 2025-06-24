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
    fakeUseUpdateModerationStatus = sinon.stub().returns({});

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
    },
    {
      userInfo: {
        display_name: 'Jane Doe',
      },
      annotationUser: 'acct:foo@example.com',
      expectedDisplayName: 'Jane Doe',
    },
    {
      userInfo: undefined,
      annotationUser: 'invalid',
      expectedDisplayName: 'invalid',
    },
  ].forEach(({ userInfo, annotationUser, expectedDisplayName }) => {
    it('renders expected username', () => {
      fakeAnnotation.user_info = userInfo;
      fakeAnnotation.user = annotationUser;

      const wrapper = createComponent();

      assert.equal(
        wrapper.find('AnnotationUser').prop('displayName'),
        expectedDisplayName,
      );
    });
  });

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

  it('renders annotation dates in AnnotationTimestamps', () => {
    fakeAnnotation.created = '2025-01-01';
    fakeAnnotation.updated = '2025-01-05';

    const wrapper = createComponent();
    const timestamps = wrapper.find('AnnotationTimestamps');

    assert.equal(timestamps.prop('annotationCreated'), fakeAnnotation.created);
    assert.equal(timestamps.prop('annotationUpdated'), fakeAnnotation.updated);
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
      fakeUseUpdateModerationStatus.returns({
        updateModerationStatus: fakeUpdateModerationStatus,
      });

      const wrapper = createComponent();
      await wrapper.find('ModerationStatusSelect').props().onChange(status);

      assert.calledWith(fakeUpdateModerationStatus, status);
      assert.calledWith(fakeOnStatusChange, status);
    });
  });

  [true, false].forEach(updating => {
    it('disables ModerationStatusSelect when updating moderation status', () => {
      fakeUseUpdateModerationStatus.returns({ updating });
      const wrapper = createComponent();

      assert.equal(
        wrapper.find('ModerationStatusSelect').prop('disabled'),
        updating,
      );
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
