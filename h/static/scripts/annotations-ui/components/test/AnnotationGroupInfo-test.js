import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import AnnotationGroupInfo, { $imports } from '../AnnotationGroupInfo';

describe('AnnotationGroupInfo', () => {
  let fakeGroup;

  const createAnnotationGroupInfo = props => {
    return mount(<AnnotationGroupInfo group={fakeGroup} {...props} />);
  };

  beforeEach(() => {
    fakeGroup = {
      name: 'My Group',
      links: {
        html: 'https://www.example.com',
      },
      type: 'private',
    };

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('group link', () => {
    it('should show a link to the group for extant, first-party groups', () => {
      const wrapper = createAnnotationGroupInfo();

      const groupLink = wrapper.find('a');

      assert.equal(groupLink.prop('href'), fakeGroup.links.html);
      assert.include(groupLink.text(), fakeGroup.name);
    });

    it('should display a group icon for private and restricted groups', () => {
      const wrapper = createAnnotationGroupInfo();

      assert.isTrue(wrapper.find('GroupsIcon').exists());
    });

    it('should display a public/world icon for open groups', () => {
      fakeGroup.type = 'open';
      const wrapper = createAnnotationGroupInfo();

      assert.isTrue(wrapper.find('GlobeIcon').exists());
    });

    it('should not show a link to third-party groups', () => {
      // Third-party groups have no `html` link
      const wrapper = createAnnotationGroupInfo({
        group: { name: 'A Group', links: {} },
      });
      const groupLink = wrapper.find('.AnnotationGroupInfo__group');

      assert.notOk(groupLink.exists());
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createAnnotationGroupInfo(),
    }),
  );
});
