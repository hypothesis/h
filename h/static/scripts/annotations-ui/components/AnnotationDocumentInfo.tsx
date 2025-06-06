import { Link } from '@hypothesis/frontend-shared';

export type AnnotationDocumentInfoProps = {
  /** The domain associated with the document */
  domain?: string;
  /** A direct link to the document */
  link?: string;
  title: string;
};
/**
 * Render some metadata about an annotation's document and link to it
 * if a link is available.
 */
export default function AnnotationDocumentInfo({
  domain,
  link,
  title,
}: AnnotationDocumentInfoProps) {
  return (
    <div className="flex gap-x-1">
      <div className="text-color-text-light">
        on &quot;
        {link ? (
          <Link href={link} target="_blank" underline="none">
            {title}
          </Link>
        ) : (
          <span>{title}</span>
        )}
        &quot;
      </div>
      {domain && <span className="text-color-text-light">({domain})</span>}
    </div>
  );
}
