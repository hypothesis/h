import { Link } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { Link as RouterLink, useRoute } from 'wouter-preact';

import type { Group } from '../config';
import { Config } from '../config';
import { routes } from '../routes';
import { useContext } from 'preact/hooks';

type TabLinkProps = {
  href: string;
  children: ComponentChildren;
  testId?: string;
};

function TabLink({ children, href, testId }: TabLinkProps) {
  const [selected] = useRoute(href);
  return (
    <RouterLink
      href={href}
      className={classnames({
        'focus-visible-ring whitespace-nowrap flex items-center font-semibold rounded px-2 py-1 gap-x-2':
          true,
        'text-grey-1 bg-grey-7': selected,
      })}
      data-testid={testId}
    >
      {children}
    </RouterLink>
  );
}

export type GroupFormHeaderProps = {
  group: Group | null;
  title: string;
};

export default function GroupFormHeader({
  group,
  title,
}: GroupFormHeaderProps) {
  const config = useContext(Config);
  const enableMembers = config?.features.group_members;
  const enableModeration = config?.features.group_moderation;

  // This should be replaced with a proper URL generation function that handles
  // escaping etc.
  const editLink = group
    ? routes.groups.edit.replace(':pubid', group.pubid)
    : null;
  const editMembersLinks = group
    ? routes.groups.editMembers.replace(':pubid', group.pubid)
    : null;
  const moderationLinks = group
    ? routes.groups.moderation.replace(':pubid', group.pubid)
    : null;

  return (
    <div className="mb-4 pb-1 border-b border-b-text-grey-6">
      {group && (
        <div className="mb-4">
          <Link
            classes="text-grey-7"
            href={group.link}
            underline="always"
            data-testid="activity-link"
          >
            View group activity
          </Link>
        </div>
      )}
      <div className="flex gap-x-2 py-2 items-center">
        <h1 className="text-grey-7 text-xl/none" data-testid="header">
          {title}
        </h1>
        <div className="grow" />
        {enableMembers && editLink && (
          <TabLink testId="settings-link" href={editLink}>
            Settings
          </TabLink>
        )}
        {enableMembers && editMembersLinks && (
          <TabLink testId="members-link" href={editMembersLinks}>
            Members
          </TabLink>
        )}
        {enableModeration && moderationLinks && (
          <TabLink testId="moderation-link" href={moderationLinks}>
            Moderation
          </TabLink>
        )}
      </div>
    </div>
  );
}
