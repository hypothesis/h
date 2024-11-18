import { Route, Switch } from 'wouter-preact';
import { useMemo, useState } from 'preact/hooks';

import CreateEditGroupForm from './CreateEditGroupForm';
import EditGroupMembersForm from './EditGroupMembersForm';
import Router from './Router';
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

  // Saved group details. Extracted out of `config` so we can update them after
  // saving changes to the backend.
  const [group, setGroup] = useState(config.context.group);

  return (
    <>
      {stylesheetLinks}
      <Config.Provider value={config}>
        <Router>
          <Switch>
            <Route path={routes.groups.new}>
              <CreateEditGroupForm group={group} onUpdateGroup={setGroup} />
            </Route>
            <Route path={routes.groups.edit}>
              <CreateEditGroupForm group={group} onUpdateGroup={setGroup} />
            </Route>
            <Route path={routes.groups.editMembers}>
              <EditGroupMembersForm group={group!} />
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
