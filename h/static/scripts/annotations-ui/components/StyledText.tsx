import classnames from 'classnames';
import type { ComponentChildren, JSX } from 'preact';

export type StyledTextProps = JSX.HTMLAttributes<HTMLDivElement> & {
  children: ComponentChildren;
  classes?: string;
};

/**
 * Render children as styled text: basic prose styling for HTML
 */
export default function StyledText({
  children,
  classes,
  ...restProps
}: StyledTextProps) {
  // The language for the quote may be different than the client's UI (set by
  // `<html lang="...">`).
  //
  // Use a blank string to indicate that it is unknown and it is up to the user
  // agent to pick a default or analyze the content and guess.
  //
  // For web documents we could do better here and gather language information
  // as part of the annotation anchoring process.
  const documentLanguage = '';

  return (
    <div
      dir="auto"
      lang={documentLanguage}
      className={classnames('StyledText', classes)}
      {...restProps}
    >
      {children}
    </div>
  );
}
