import { Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import type { Group } from '../config';
import { GroupFormsConfig } from '../config';
import { routes } from '../routes';
import FormHeader from './FormHeader';
import TabLinks from './TabLinks';

export type GroupFormHeaderProps = {
  group: Group | null;

  /** Fallback title used if there is no group. */
  title: string;
};

export default function GroupFormHeader({
  group,
  title,
}: GroupFormHeaderProps) {
  const config = useContext(GroupFormsConfig);
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
            href={group.link}
            underline="always"
            data-testid="activity-link"
            variant="text"
          >
            View group activity
          </Link>
        </div>
      )}
      <div className="flex gap-x-2 py-2 items-center">
        <FormHeader variant="compact" data-testid="header">
          {group?.name ?? title}
        </FormHeader>
        <div className="grow" />
        <TabLinks>
          {enableMembers && editLink && (
            <TabLinks.Link testId="settings-link" href={editLink}>
              Settings
            </TabLinks.Link>
          )}
          {enableMembers && editMembersLinks && (
            <TabLinks.Link testId="members-link" href={editMembersLinks}>
              Members
            </TabLinks.Link>
          )}
          {enableModeration && moderationLinks && (
            <TabLinks.Link testId="moderation-link" href={moderationLinks}>
              Moderation
            </TabLinks.Link>
          )}
        </TabLinks>
      </div>
    </div>
  );
}
