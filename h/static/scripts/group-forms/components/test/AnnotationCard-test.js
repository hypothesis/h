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

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '@hypothesis/annotation-ui': {
        AnnotationTimestamps: () => null,
        AnnotationUser: () => null,
        AnnotationGroupInfo: () => null,
        MarkdownView: () => null,
        AnnotationShareControl: () => null,
      },
    });
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <AnnotationCard annotation={fakeAnnotation} />
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
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createComponent() }),
  );
});
