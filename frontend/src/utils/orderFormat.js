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

// Shows a date in the viewer's time zone. Timestamps (order_date, removed_at) convert to
// the local day; calendar dates (YYYY-MM-DD, used by estimates) are parsed as local so
// they don't shift a day.
export const formatDate = (value) => {
  if (!value) return 'N/A';
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value);
  return date.toLocaleDateString();
};

// The likely range around the best guess, or null when it is a single day
export const formatEstRange = (completionData) => {
  if (!completionData?.estimated_date) return null;
  const { estimated_date, range_start_date = estimated_date, range_end_date = estimated_date } = completionData;
  if (range_start_date === range_end_date) return null;
  return `${formatDate(range_start_date)} – ${formatDate(range_end_date)}`;
};

// The best guess, followed by the likely range when there is one
export const formatEstCompletion = (completionData) => {
  if (!completionData) return 'N/A';
  const { days_remaining, estimated_date } = completionData;
  if (estimated_date) {
    const range = formatEstRange(completionData);
    return range ? `${formatDate(estimated_date)} (likely ${range})` : formatDate(estimated_date);
  }
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
