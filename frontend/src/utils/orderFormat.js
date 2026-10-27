// frontend/src/utils/orderFormat.js
// Display helpers shared by the search results, saved orders and order details pages.

// Labels for the statuses in OrderRecord.STATUS_CHOICES
const STATUS_LABELS = {
  NEW: 'New',
  PARTS_PULLED: 'Parts Pulled',
  ON_BENCH: 'On Bench',
  TESTING: 'Testing',
  QUALITY_CONTROL: 'Quality Control',
  PASSED_QC: 'Passed QC',
  PASSED_QC_AWAITING_PAYMENT: 'Passed QC – Awaiting Payment',
  COMPLETED_WAITING_BASE: 'Completed – Waiting for Base',
};

// Matches DONE_STATUSES in orders/estimation.py
const FINISHED_STATUSES = ['PASSED_QC', 'PASSED_QC_AWAITING_PAYMENT', 'COMPLETED_WAITING_BASE'];

export const formatStatus = (status) => STATUS_LABELS[status] || status;

export const isFinished = (status) => FINISHED_STATUSES.includes(status);

// MUI color for a status: waiting in the queue, being built, or finished
export const statusColor = (status) => {
  if (status === 'NEW') return 'primary';
  if (isFinished(status)) return 'success';
  return 'warning';
};

// Estimates are calendar dates (YYYY-MM-DD); parse them as local so they don't shift a day
export const formatDay = (day) => {
  if (!day) return 'N/A';
  const date = /^\d{4}-\d{2}-\d{2}$/.test(day) ? new Date(`${day}T00:00:00`) : new Date(day);
  return date.toLocaleDateString();
};

export const formatEstCompletion = (completionData) => {
  if (!completionData) return 'N/A';
  const { days_remaining, estimated_date, range_end_date } = completionData;
  if (estimated_date && range_end_date && range_end_date !== estimated_date) {
    return `${formatDay(estimated_date)} – ${formatDay(range_end_date)}`;
  }
  if (estimated_date) return formatDay(estimated_date);
  if (days_remaining !== undefined && days_remaining !== null) {
    if (days_remaining < 0) return 'Overdue';
    if (days_remaining === 0) return 'Today';
    if (days_remaining === 1) return 'Tomorrow';
    return `${days_remaining} days`;
  }
  return 'N/A';
};

const CONFIDENCE_LABELS = { LOW: 'Low', MEDIUM: 'Medium', HIGH: 'High' };

export const formatConfidence = (level) => CONFIDENCE_LABELS[level] || 'N/A';
