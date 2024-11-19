import { useEffect } from 'preact/hooks';

/** Count of components with unsaved changes. */
let unsavedCount = 0;

function preventUnload(e: BeforeUnloadEvent) {
  e.preventDefault();
  e.returnValue = '';
}

/**
 * Return true if any active components have indicated they have unsaved changes
 * using {@link useUnsavedChanges}.
 */
export function hasUnsavedChanges() {
  return unsavedCount > 0;
}

/**
 * Hook that registers the current component as having unsaved changes that
 * would be lost in the event of a navigation.
 *
 * @param hasUnsavedChanges - True if current component has unsaved changes
 * @param window_ - Test seam
 */
export function useUnsavedChanges(hasUnsavedData: boolean, window_ = window) {
  useEffect(() => {
    if (hasUnsavedData) {
      unsavedCount += 1;
      if (unsavedCount === 1) {
        window_.addEventListener('beforeunload', preventUnload);
      }
    }
    return () => {
      if (hasUnsavedData) {
        unsavedCount -= 1;
        if (unsavedCount === 0) {
          window_.removeEventListener('beforeunload', preventUnload);
        }
      }
    };
  }, [hasUnsavedData, window_]);
}
