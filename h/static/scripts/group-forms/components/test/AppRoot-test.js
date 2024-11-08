import { mount } from 'enzyme';
import { useContext } from 'preact/hooks';

import { $imports, default as AppRoot } from '../AppRoot';
import { Config } from '../../config';

describe('AppRoot', () => {
  let configContext;
  const config = { styles: [] };

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

  it('passes config to route', () => {
    history.pushState({}, null, '/groups/new');
    try {
      mount(<AppRoot config={config} />);
      assert.strictEqual(configContext, config);
    } finally {
      history.back();
    }
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
      history.pushState({}, '', path);
      try {
        const wrapper = mount(<AppRoot config={config} />);
        assert.isTrue(wrapper.exists(selector));
      } finally {
        history.back();
      }
    });
  });
});
