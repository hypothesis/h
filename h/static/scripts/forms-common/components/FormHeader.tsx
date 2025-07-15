import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type FormHeaderProps = {
  children: ComponentChildren;
  classes?: string;
  variant?: 'default' | 'compact';
};

/** Page title for forms. */
export default function FormHeader({
  children,
  classes,
  variant = 'default',
}: FormHeaderProps) {
  return (
    <h1
      className={classnames(
        'text-grey-7 text-xl/none',
        variant === 'default' && 'my-8',
        classes,
      )}
    >
      {children}
    </h1>
  );
}
