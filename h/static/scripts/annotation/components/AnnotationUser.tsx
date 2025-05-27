import { Link } from '@hypothesis/frontend-shared';

type AnnotationUserProps = {
  authorLink?: string;
  displayName: string;
};

/**
 * Display information about an annotation's user. Link to the user's
 * activity if `authorLink` is present.
 */
function AnnotationUser({ authorLink, displayName }: AnnotationUserProps) {
  const user = <h3 className="text-color-text font-bold">{displayName}</h3>;

  if (authorLink) {
    return (
      <Link href={authorLink} target="_blank" underline="none" variant="custom">
        {user}
      </Link>
    );
  }

  return <div>{user}</div>;
}

export default AnnotationUser;
