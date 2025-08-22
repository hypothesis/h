import { IconButton, CopyIcon, CheckIcon } from '@hypothesis/frontend-shared';
import { useState, useEffect } from 'preact/hooks';

export type CopyButtonProps = {
  /** Tooltip for the copy button. */
  title: string;

  /** Text to be copied. */
  value: string;
};

/**
 * Button for copying text to the clipboard.
 *
 * When text is copied, the icon briefly changes to indicate success.
 */
export default function CopyButton({ title, value }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const copyValue = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
  };

  useEffect(() => {
    if (!copied) {
      return () => {};
    }
    const timeout = setTimeout(() => setCopied(false), 1000);
    return () => clearTimeout(timeout);
  }, [copied]);

  return (
    <IconButton
      icon={copied ? CheckIcon : CopyIcon}
      title={title}
      onClick={copyValue}
      variant="dark"
    />
  );
}
