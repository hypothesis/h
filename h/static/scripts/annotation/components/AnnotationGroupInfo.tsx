import { Link, GlobeIcon, GroupsIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';

import type { Group } from '../../group-forms/config';

export type AnnotationGroupInfoProps = {
  /** Group to which the annotation belongs */
  group: Group;
};

/**
 * Render information about what group an annotation is in.
 *
 * @param {AnnotationGroupInfoProps} props
 */
function AnnotationGroupInfo({ group }: AnnotationGroupInfoProps) {
  const linkToGroup = group.link;

  return (
    <Link
      // The light-text hover color is not a standard color for a Link, so
      // a custom variant is used
      classes={classnames('text-color-text-light hover:text-color-text-light')}
      href={linkToGroup}
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
  );
}

export default AnnotationGroupInfo;
