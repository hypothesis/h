import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type FormContainerProps = {
  children: ComponentChildren;
  classes?: string;
};

/**
 * Container that sets default styles for a form.
 */
export default function FormContainer({
  children,
  classes,
}: FormContainerProps) {
  return (
    <div className={classnames('text-grey-6 text-sm/relaxed', classes)}>
      {children}
    </div>
  );
}
