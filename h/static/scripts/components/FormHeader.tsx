import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type FormHeaderProps = {
  children: ComponentChildren;
  classes?: string;
  variant?: 'default' | 'compact';
  center?: boolean;
};

/** Page title for forms. */
export default function FormHeader({
  children,
  classes,
  center,
  variant = 'default',
}: FormHeaderProps) {
  return (
    <h1
      className={classnames(
        'text-grey-7 text-xl/none',
        center && 'text-center',
        variant === 'default' && 'my-8',
        classes,
      )}
    >
      {children}
    </h1>
  );
}
