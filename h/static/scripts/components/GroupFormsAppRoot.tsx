import { useState } from 'preact/hooks';
import { Route, Switch } from 'wouter-preact';

import type { GroupFormsConfigObject } from '../config';
import { GroupFormsConfig } from '../config';
import { routes } from '../routes';
import CreateEditGroupForm from './CreateEditGroupForm';
import EditGroupMembersForm from './EditGroupMembersForm';
import GroupModeration from './GroupModeration';
import Router from './Router';

export type GroupFormsAppRootProps = {
  config: GroupFormsConfigObject;
};

export default function GroupFormsAppRoot({ config }: GroupFormsAppRootProps) {
  // Saved group details. Extracted out of `config` so we can update them after
  // saving changes to the backend.
  const [group, setGroup] = useState(config.context.group);

  return (
    <GroupFormsConfig.Provider value={config}>
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
          <Route path={routes.groups.moderation}>
            <GroupModeration group={group!} />
          </Route>
          <Route>
            <h1 data-testid="unknown-route">Page not found</h1>
          </Route>
        </Switch>
      </Router>
    </GroupFormsConfig.Provider>
  );
}
