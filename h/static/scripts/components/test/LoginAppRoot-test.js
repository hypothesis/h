import { mount } from '@hypothesis/frontend-testing';
import { useContext } from 'preact/hooks';

import { LoginFormsConfig } from '../../config';
import { $imports, default as LoginAppRoot } from '../LoginAppRoot';

describe('LoginAppRoot', () => {
  let config;
  let configContext;

  beforeEach(() => {
    const mockComponent = name => {
      function MockRoute() {
        configContext = useContext(LoginFormsConfig);
        return null;
      }
      MockRoute.displayName = name;
      return MockRoute;
    };

    configContext = null;

    config = { csrfToken: 'fake-csrf-token', features: {} };

    $imports.$mock({
      './AccountSettingsForms': mockComponent('AccountSettingsForms'),
      './DeveloperForm': mockComponent('DeveloperForm'),
      './LoginForm': mockComponent('LoginForm'),
      './ProfileForm': mockComponent('ProfileForm'),
      './SignupForm': mockComponent('SignupForm'),
      './SignupSelectForm': mockComponent('SignupSelectForm'),
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(<LoginAppRoot config={config} />);
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
        const wrapper = mount(<LoginAppRoot config={configWithFlash} />);

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
        const wrapper = mount(<LoginAppRoot config={config} />);
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
        const wrapper = mount(<LoginAppRoot config={configWithFlash} />);
        wrapper.find('[data-testid="dismiss-0"]').simulate('click');
        assert.isFalse(wrapper.find('[data-testid="toast-success"]').exists());
      });
    });
  });

  [
    {
      path: '/account/developer',
      selector: 'DeveloperForm',
    },
    {
      path: '/account/profile',
      selector: 'ProfileForm',
    },
    {
      path: '/account/settings',
      selector: 'AccountSettingsForms',
      props: {},
    },
    {
      path: '/login',
      selector: 'LoginForm',
      props: {
        enableSocialLogin: false,
      },
    },
    {
      path: '/login',
      selector: 'LoginForm',
      features: {
        log_in_with_google: true,
      },
      props: {
        enableSocialLogin: true,
      },
    },
    // "/signup" shows email signup form if all social logins are disabled
    {
      path: '/signup',
      selector: 'SignupForm',
    },
    // "/signup" shows signup provider form if any social logins are enabled
    {
      path: '/signup',
      features: {
        log_in_with_orcid: true,
      },
      selector: 'SignupSelectForm',
    },
    {
      path: '/signup',
      features: {
        log_in_with_google: true,
      },
      selector: 'SignupSelectForm',
    },
    {
      path: '/signup',
      features: {
        log_in_with_facebook: true,
      },
      selector: 'SignupSelectForm',
    },
    {
      path: '/signup/email',
      selector: 'SignupForm',
    },
    {
      path: '/signup/orcid',
      selector: 'SignupForm',
      props: {
        idProvider: 'orcid',
      },
    },
    {
      path: '/signup/google',
      selector: 'SignupForm',
      props: {
        idProvider: 'google',
      },
    },
    {
      path: '/signup/facebook',
      selector: 'SignupForm',
      props: {
        idProvider: 'facebook',
      },
    },
  ].forEach(({ path, selector, features = {}, props = {} }) => {
    it(`renders expected component for URL (${path})`, () => {
      config.features = features;

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
