import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { Link as RouterLink, useRoute } from 'wouter-preact';

import type { Group } from '../config';
import { routes } from '../routes';

type TabLinkProps = {
  href: string;
  children: ComponentChildren;
};

function TabLink({ children, href }: TabLinkProps) {
  const [selected] = useRoute(href);
  return (
    <RouterLink
      href={href}
      className={classnames({
        'focus-visible-ring whitespace-nowrap flex items-center font-semibold rounded px-2 py-1 gap-x-2':
          true,
        'text-grey-1 bg-grey-7': selected,
      })}
    >
      {children}
    </RouterLink>
  );
}

export type GroupFormHeaderProps = {
  group: Group;
};

export default function GroupFormHeader({ group }: GroupFormHeaderProps) {
  // This should be replaced with a proper URL generation function that handles
  // escaping etc.
  const editLink = routes.groups.edit.replace(':pubid', group.pubid);
  const editMembersLinks = routes.groups.editMembers.replace(
    ':pubid',
    group.pubid,
  );

  return (
    <div className="flex gap-x-2 justify-end py-2">
      <TabLink href={editLink}>Settings</TabLink>
      <TabLink href={editMembersLinks}>Members</TabLink>
    </div>
  );
}
