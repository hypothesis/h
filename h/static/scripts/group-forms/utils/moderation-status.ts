import type { ModerationStatus } from '../components/ModerationStatusSelect';

export const moderationStatusToLabel: Record<ModerationStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  DENIED: 'Denied',
  SPAM: 'Spam',
} as const;

Object.freeze(moderationStatusToLabel);
