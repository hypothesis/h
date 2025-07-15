import { Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import FormHeader from '../../forms-common/components/FormHeader';
import TabLinks from '../../forms-common/components/TabLinks';
import type { Group } from '../config';
import { Config } from '../config';
import { routes } from '../routes';

export type GroupFormHeaderProps = {
  group: Group | null;

  /** Fallback title used if there is no group. */
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
