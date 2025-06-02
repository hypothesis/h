import type { ComponentChildren } from 'preact';
import { useCallback, useState } from 'preact/hooks';
import { Router as BaseRouter } from 'wouter-preact';
import { useBrowserLocation } from 'wouter-preact/use-browser-location';

import { hasUnsavedChanges } from '../unsaved-changes';
import WarningDialog from './WarningDialog';

export type RouterProps = {
  children: ComponentChildren;
};

/**
 * A wrapper around Wouter's `Router` component which intercepts navigations
 * triggered by router links and allows the user to cancel them if the
 * navigation may lose unsaved changes.
 */
export default function Router({ children }: RouterProps) {
  const [location, origSetLocation] = useBrowserLocation();
  const [pendingURL, setPendingURL] = useState<string | null>(null);

  const setLocation = useCallback(
    (url: string) => {
      if (!hasUnsavedChanges()) {
        origSetLocation(url);
        return;
      }
      setPendingURL(url);
    },
    [origSetLocation],
  );
  const hook: () => [string, typeof setLocation] = useCallback(
    () => [location, setLocation],
    [location, setLocation],
  );

  return (
    <>
      <BaseRouter hook={hook}>{children}</BaseRouter>
      {pendingURL && (
        <WarningDialog
          title="Leave page?"
          onCancel={() => setPendingURL(null)}
          onConfirm={() => {
            setPendingURL(null);
            origSetLocation(pendingURL);
          }}
          confirmAction="Leave page"
          message="This will lose unsaved changes."
        />
      )}
    </>
  );
}
