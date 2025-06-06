import { Link, GlobeIcon, GroupsIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';

import type { Group } from '../helpers/groups';

export type AnnotationGroupInfoProps = {
  /** Group to which the annotation belongs */
  group: Group;
};

/**
 * Render information about what group an annotation is in.
 */
export default function AnnotationGroupInfo({
  group,
}: AnnotationGroupInfoProps) {
  // Only show the name of the group and link to it if there is a
  // URL (link) returned by the API for this group. Some groups do not have links
  const linkToGroup = group?.links.html;

  return (
    <>
      {group && linkToGroup && (
        <Link
          // The light-text hover color is not a standard color for a Link, so
          // a custom variant is used
          classes={classnames(
            'text-color-text-light hover:text-color-text-light',
          )}
          href={group.links.html}
          target="_blank"
          underline="hover"
          variant="custom"
        >
          <div className="flex items-baseline gap-x-1">
            {group.type === 'open' ? (
              <GlobeIcon className="w-2.5 h-2.5" />
            ) : (
              <GroupsIcon className="w-2.5 h-2.5" />
            )}
            <span>{group.name}</span>
          </div>
        </Link>
      )}
    </>
  );
}
