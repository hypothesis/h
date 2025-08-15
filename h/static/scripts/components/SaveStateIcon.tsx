import { SpinnerSpokesIcon, CheckIcon } from '@hypothesis/frontend-shared';

export type SaveStateIconProps = {
  state: 'unsaved' | 'saving' | 'saved';
};

/**
 * An accessible save status icon.
 *
 * This can be in one of three states, set via the `state` prop:
 *
 *  - "unsaved" - There are no changes, or the changes are unsaved
 *  - "saving" - Changes are currently being saved
 *  - "saved" - Changes were successfully saved
 */
export default function SaveStateIcon({ state }: SaveStateIconProps) {
  return (
    <div role="status">
      {state === 'saving' && (
        // We use the `SpinnerSpokesIcon` component rather than `Spinner`
        // because `Spinner` doesn't currently support aria-label. Also we want
        // this component to have the same layout in the saving and saved
        // states.
        <SpinnerSpokesIcon aria-label="Saving changes..." />
      )}
      {state === 'saved' && <CheckIcon aria-label="Changes saved" />}
    </div>
  );
}
