import { mount } from '@hypothesis/frontend-testing';
import { useContext } from 'preact/hooks';

import { $imports, default as AppRoot } from '../AppRoot';
import { Config } from '../../config';

describe('AppRoot', () => {
  let configContext;

  const config = { context: { group: { pubid: '1234' } }, styles: [] };

  beforeEach(() => {
    const mockComponent = name => {
      function MockRoute() {
        configContext = useContext(Config);
        return null;
      }
      MockRoute.displayName = name;
      return MockRoute;
    };

    configContext = null;

    $imports.$mock({
      './CreateEditGroupForm': mockComponent('CreateEditGroupForm'),
      './EditGroupMembersForm': mockComponent('EditGroupMembersForm'),
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders style links', () => {
    config.styles = ['/static/styles/foo.css'];
    const links = mount(<AppRoot config={config} />).find('link');
    assert.equal(links.length, 1);
    assert.equal(links.at(0).prop('rel'), 'stylesheet');
    assert.equal(links.at(0).prop('href'), '/static/styles/foo.css');
  });

  /** Navigate to `path`, run `callback` and then reset the location. */
  function navigate(path, callback) {
    history.pushState({}, null, path);
    try {
      callback();
    } finally {
      history.back();
    }
  }

  it('passes config to route', () => {
    navigate('/groups/new', () => {
      mount(<AppRoot config={config} />);
      assert.strictEqual(configContext, config);
    });
  });

  it('passes saved group to group settings route', () => {
    navigate('/groups/1234/edit', () => {
      const wrapper = mount(<AppRoot config={config} />);
      assert.equal(
        wrapper.find('CreateEditGroupForm').prop('group'),
        config.context.group,
      );
    });
  });

  it('passes updated group to group settings route', () => {
    navigate('/groups/1234/edit', () => {
      const wrapper = mount(<AppRoot config={config} />);
      const updatedGroup = { name: 'foobar' };
      wrapper.find('CreateEditGroupForm').prop('onUpdateGroup')(updatedGroup);
      wrapper.update();
      assert.equal(
        wrapper.find('CreateEditGroupForm').prop('group'),
        updatedGroup,
      );
    });
  });

  [
    {
      path: '/groups/new',
      selector: 'CreateEditGroupForm',
    },
    {
      path: '/groups/1234/edit',
      selector: 'CreateEditGroupForm',
    },
    {
      path: '/groups/1234/edit/members',
      selector: 'EditGroupMembersForm',
    },
    {
      path: '/unknown',
      selector: '[data-testid="unknown-route"]',
    },
  ].forEach(({ path, selector }) => {
    it(`renders expected component for URL (${path})`, () => {
      navigate(path, () => {
        const wrapper = mount(<AppRoot config={config} />);
        const component = wrapper.find(selector);
        assert.isTrue(component.exists());
      });
    });
  });
});
