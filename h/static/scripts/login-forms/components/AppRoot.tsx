import { ToastMessages, useToastMessages } from '@hypothesis/frontend-shared';
import type { ToastMessageData } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { Route, Switch } from 'wouter-preact';

import Router from '../../forms-common/components/Router';
import type { ConfigObject } from '../config';
import { Config } from '../config';
import { routes } from '../routes';
import AccountSettingsForms from './AccountSettingsForms';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';
import SignupSelectForm from './SignupSelectForm';

function toastMessagesFromConfig(config: ConfigObject): ToastMessageData[] {
  const flashMessages = config.flashMessages ?? [];
  return flashMessages.map(msg => ({ ...msg, autoDismiss: false }));
}

export type AppRootProps = {
  config: ConfigObject;
};

export default function AppRoot({ config }: AppRootProps) {
  const initialToasts = useMemo(
    () => toastMessagesFromConfig(config),
    [config],
  );
  const { toastMessages, dismissToastMessage } =
    useToastMessages(initialToasts);

  const enableSocialLogin = Boolean(
    config.features.log_in_with_orcid ||
      config.features.log_in_with_google ||
      config.features.log_in_with_facebook,
  );

  return (
    <div>
      <ToastMessages
        messages={toastMessages}
        onMessageDismiss={dismissToastMessage}
      />
      <Config.Provider value={config}>
        <Router>
          <Switch>
            <Route path={routes.login}>
              <LoginForm enableSocialLogin={enableSocialLogin} />
            </Route>
            <Route path={routes.signup}>
              {enableSocialLogin && <SignupSelectForm />}
              {!enableSocialLogin && <SignupForm />}
            </Route>
            <Route path={routes.signupWithEmail}>
              <SignupForm />
            </Route>
            <Route path={routes.signupWithFacebook}>
              <SignupForm idProvider="facebook" />
            </Route>
            <Route path={routes.signupWithGoogle}>
              <SignupForm idProvider="google" />
            </Route>
            <Route path={routes.signupWithORCID}>
              <SignupForm idProvider="orcid" />
            </Route>
            <Route path={routes.accountSettings}>
              <AccountSettingsForms />
            </Route>
            <Route>
              <h1 data-testid="unknown-route">Page not found</h1>
            </Route>
          </Switch>
        </Router>
      </Config.Provider>
    </div>
  );
}
