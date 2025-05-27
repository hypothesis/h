import { Link } from '@hypothesis/frontend-shared';

export type TagListItemProps = {
  /** If present, tag will be linked to this URL  */
  href?: string;

  tag: string;
};

/**
 * Render a single annotation tag as part of a list of tags
 */
export default function TagListItem({ href, tag }: TagListItemProps) {
  return (
    <li className="flex items-center border rounded bg-grey-0">
      <div className="grow px-1.5 py-1 touch:p-2">
        {href ? (
          <Link
            variant="text-light"
            href={href}
            lang=""
            target="_blank"
            aria-label={`Tag: ${tag}`}
            title={`View annotations with tag: ${tag}`}
            underline="none"
          >
            {tag}
          </Link>
        ) : (
          <span
            className="text-color-text-light cursor-default"
            aria-label={`Tag: ${tag}`}
            lang=""
          >
            {tag}
          </span>
        )}
      </div>
    </li>
  );
}
