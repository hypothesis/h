import { mockImportedComponents, mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import AnnotationCard, { $imports } from '../AnnotationCard';

describe('AnnotationCard', () => {
  let fakeConfig;
  let fakeAnnotation;
  let fakeQuote;
  let fakeUsername;

  beforeEach(() => {
    fakeConfig = {
      context: {},
    };
    fakeAnnotation = {
      tags: [],
      links: {},
    };

    fakeQuote = sinon.stub().callsFake(anno => anno.quote);
    fakeUsername = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/annotation-metadata': {
        username: fakeUsername,
        quote: fakeQuote,
      },
      '@hypothesis/annotation-ui': {
        AnnotationTimestamps: () => null,
        AnnotationUser: () => null,
        AnnotationGroupInfo: () => null,
        MarkdownView: () => null,
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
      usernameResult: undefined,
      annotationUser: 'acct:foo@example.com',
      expectedDisplayName: 'acct:foo@example.com',
    },
    {
      userInfo: {
        display_name: 'Jane Doe',
      },
      usernameResult: undefined,
      annotationUser: 'acct:foo@example.com',
      expectedDisplayName: 'Jane Doe',
    },
    {
      userInfo: undefined,
      usernameResult: 'john',
      annotationUser: 'acct:john@example.com',
      expectedDisplayName: 'john',
    },
  ].forEach(
    ({ userInfo, usernameResult, annotationUser, expectedDisplayName }) => {
      it('renders expected username', () => {
        fakeAnnotation.user_info = userInfo;
        fakeAnnotation.user = annotationUser;
        fakeUsername.returns(usernameResult);

        const wrapper = createComponent();

        assert.equal(
          wrapper.find('AnnotationUser').prop('displayName'),
          expectedDisplayName,
        );
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

  it('sets annotation dates in AnnotationTimestamps', () => {
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
      wrapper.find('Link').prop('href'),
      fakeAnnotation.links.incontext,
    );
  });
});
