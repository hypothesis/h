import { Route, Switch } from 'wouter-preact';
import { useMemo } from 'preact/hooks';

import CreateEditGroupForm from './CreateEditGroupForm';
import EditGroupMembersForm from './EditGroupMembersForm';
import type { ConfigObject } from '../config';
import { Config } from '../config';
import { routes } from '../routes';

export type AppRootProps = {
  config: ConfigObject;
};

export default function AppRoot({ config }: AppRootProps) {
  const stylesheetLinks = useMemo(
    () =>
      config.styles.map((stylesheetURL, index) => (
        <link
          key={`${stylesheetURL}${index}`}
          rel="stylesheet"
          href={stylesheetURL}
        />
      )),
    [config],
  );

  return (
    <>
      {stylesheetLinks}
      <Config.Provider value={config}>
        <Switch>
          <Route path={routes.groups.new}>
            <CreateEditGroupForm />
          </Route>
          <Route path={routes.groups.edit}>
            <CreateEditGroupForm />
          </Route>
          <Route path={routes.groups.editMembers}>
            <EditGroupMembersForm />
          </Route>
          <Route>
            <h1 data-testid="unknown-route">Page not found</h1>
          </Route>
        </Switch>
      </Config.Provider>
    </>
  );
}
