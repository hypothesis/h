import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { useContext } from 'preact/hooks';

import { Config } from '../../config';
import { $imports, default as AppRoot } from '../AppRoot';

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
      './LoginForm': mockComponent('LoginForm'),
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(<AppRoot config={config} />);
  }

  it('renders style links', () => {
    config.styles = ['/static/styles/foo.css'];

    const links = createComponent().find('link');

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
    navigate('/login', () => {
      createComponent();

      assert.strictEqual(configContext, config);
    });
  });

  [
    {
      path: '/Login',
      selector: 'LoginForm',
    },
  ].forEach(({ path, selector }) => {
    it(`renders expected component for URL (${path})`, () => {
      navigate(path, () => {
        const wrapper = createComponent();
        const component = wrapper.find(selector);

        assert.isTrue(component.exists());
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: createComponent }),
  );
});
