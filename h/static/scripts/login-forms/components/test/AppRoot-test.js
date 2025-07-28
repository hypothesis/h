import { mount } from '@hypothesis/frontend-testing';
import { useContext } from 'preact/hooks';

import { Config } from '../../config';
import { $imports, default as AppRoot } from '../AppRoot';

describe('AppRoot', () => {
  let configContext;

  const config = { csrfToken: 'fake-csrf-token' };

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
      './SignupForm': mockComponent('SignupForm'),
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(<AppRoot config={config} />);
  }

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

  describe('flash messages', () => {
    beforeEach(() => {
      $imports.$mock({
        './LoginForm': () => null,
        '@hypothesis/frontend-shared': {
          ToastMessages: ({ messages, onMessageDismiss }) => (
            <div data-testid="toast-messages">
              {messages.map((msg, i) => (
                <div key={i} data-testid={`toast-${msg.type}`}>
                  {msg.message}
                  <button
                    data-testid={`dismiss-${i}`}
                    onClick={() => onMessageDismiss(msg.id)}
                  >
                    Dismiss
                  </button>
                </div>
              ))}
            </div>
          ),
        },
      });
    });

    it('displays flash messages from config', () => {
      const configWithFlash = {
        ...config,
        flashMessages: [
          { type: 'success', message: 'Login successful!' },
          { type: 'error', message: 'Invalid credentials' },
        ],
      };

      navigate('/login', () => {
        const wrapper = mount(<AppRoot config={configWithFlash} />);

        assert.isTrue(wrapper.find('[data-testid="toast-success"]').exists());
        assert.isTrue(wrapper.find('[data-testid="toast-error"]').exists());
        assert.equal(
          wrapper.find('[data-testid="toast-success"]').text(),
          'Login successful!Dismiss',
        );
        assert.equal(
          wrapper.find('[data-testid="toast-error"]').text(),
          'Invalid credentialsDismiss',
        );
      });
    });

    it('handles config without flash messages', () => {
      navigate('/login', () => {
        const wrapper = mount(<AppRoot config={config} />);
        assert.isFalse(wrapper.find('[data-testid="toast-success"]').exists());
        assert.isFalse(wrapper.find('[data-testid="toast-error"]').exists());
      });
    });

    it('removes toast message when dismissed', () => {
      const configWithFlash = {
        ...config,
        flashMessages: [
          { type: 'success', message: 'Login successful!', id: 'msg-1' },
        ],
      };

      navigate('/login', () => {
        const wrapper = mount(<AppRoot config={configWithFlash} />);
        wrapper.find('[data-testid="dismiss-0"]').simulate('click');
        assert.isFalse(wrapper.find('[data-testid="toast-success"]').exists());
      });
    });
  });

  [
    {
      path: '/Login',
      selector: 'LoginForm',
    },
    {
      path: '/signup',
      selector: 'SignupForm',
    },
    {
      path: '/signup/orcid',
      selector: 'SignupForm',
      props: {
        idProvider: 'orcid',
      },
    },
  ].forEach(({ path, selector, props = {} }) => {
    it(`renders expected component for URL (${path})`, () => {
      navigate(path, () => {
        const wrapper = createComponent();
        const component = wrapper.find(selector);

        assert.isTrue(component.exists());

        const actualProps = component.props();
        delete actualProps.children;
        assert.deepEqual(actualProps, props);
      });
    });
  });
});
