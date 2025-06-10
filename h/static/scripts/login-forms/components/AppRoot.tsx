import { Route, Switch } from 'wouter-preact';

import Router from '../../forms-common/components/Router';
import type { ConfigObject } from '../config';
import { Config } from '../config';
import { routes } from '../routes';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';

export type AppRootProps = {
  config: ConfigObject;
};

export default function AppRoot({ config }: AppRootProps) {
  return (
    <>
      <Config.Provider value={config}>
        <Router>
          <Switch>
            <Route path={routes.login}>
              <LoginForm />
            </Route>
            <Route path={routes.signup}>
              <SignupForm />
            </Route>
            <Route>
              <h1 data-testid="unknown-route">Page not found</h1>
            </Route>
          </Switch>
        </Router>
      </Config.Provider>
    </>
  );
}
