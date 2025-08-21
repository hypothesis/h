import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type AppContainerProps = {
  children: ComponentChildren;
  classes?: string;
};

/**
 * Container for frontend applications that sets default styles.
 */
export default function AppContainer({ children, classes }: AppContainerProps) {
  return (
    <div className={classnames('text-grey-7 text-sm/relaxed', classes)}>
      {children}
    </div>
  );
}
