import { ModalDialog, Button } from '@hypothesis/frontend-shared';

export type WarningDialogProps = {
  /** Title of the dialog. */
  title: string;

  /** Message displayed in the dialog. */
  message: string;

  /** Label for the confirmation button. */
  confirmAction: string;

  /** Callback invoked when the user confirms the action. */
  onConfirm: () => void;

  /** Callback invoked when the user aborts the action. */
  onCancel: () => void;
};

/**
 * A modal dialog that warns users about a potentially destructive action.
 */
export default function WarningDialog({
  title,
  message,
  confirmAction,
  onConfirm,
  onCancel,
}: WarningDialogProps) {
  return (
    <ModalDialog
      buttons={
        <>
          <Button data-testid="cancel-button" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            data-testid="confirm-button"
            onClick={onConfirm}
          >
            {confirmAction}
          </Button>
        </>
      }
      title={title}
      onClose={onCancel}
    >
      {message}
    </ModalDialog>
  );
}
