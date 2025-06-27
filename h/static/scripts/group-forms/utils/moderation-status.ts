import type { ModerationStatus } from './api';

export const moderationStatusToLabel: Record<ModerationStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  DENIED: 'Declined',
  SPAM: 'Spam',
} as const;

Object.freeze(moderationStatusToLabel);
