import { ToastMessages, useToastMessages } from '@hypothesis/frontend-shared';
import type { ToastMessageData } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { Route, Switch } from 'wouter-preact';

import Router from '../../forms-common/components/Router';
import type { ConfigObject } from '../config';
import { Config } from '../config';
import { routes } from '../routes';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';

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
              <LoginForm />
            </Route>
            <Route path={routes.signup}>
              <SignupForm />
            </Route>
            <Route path={routes.signupWithGoogle}>
              <SignupForm idProvider="google" />
            </Route>
            <Route path={routes.signupWithORCID}>
              <SignupForm idProvider="orcid" />
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
