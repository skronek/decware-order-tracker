import { formatStatus, statusColor, isFinished, formatDate, formatEstCompletion, formatEstRange, formatConfidence } from '../orderFormat';

describe('formatStatus', () => {
  it('labels every status the scraper records', () => {
    expect(formatStatus('NEW')).toBe('New');
    expect(formatStatus('PARTS_PULLED')).toBe('Parts Pulled');
    expect(formatStatus('ON_BENCH')).toBe('On Bench');
    expect(formatStatus('TESTING')).toBe('Testing');
    expect(formatStatus('QUALITY_CONTROL')).toBe('Quality Control');
    expect(formatStatus('PASSED_QC')).toBe('Passed QC');
    expect(formatStatus('PASSED_QC_AWAITING_PAYMENT')).toBe('Passed QC – Awaiting Payment');
    expect(formatStatus('COMPLETED_WAITING_BASE')).toBe('Completed – Waiting for Base');
  });

  it('falls back to the raw value for unknown statuses', () => {
    expect(formatStatus('SOMETHING_ELSE')).toBe('SOMETHING_ELSE');
  });
});

describe('isFinished and statusColor', () => {
  it('treats the passed-QC statuses as finished', () => {
    expect(isFinished('PASSED_QC')).toBe(true);
    expect(isFinished('PASSED_QC_AWAITING_PAYMENT')).toBe(true);
    expect(isFinished('COMPLETED_WAITING_BASE')).toBe(true);
    expect(isFinished('ON_BENCH')).toBe(false);
  });

  it('colors waiting, building and finished statuses differently', () => {
    expect(statusColor('NEW')).toBe('primary');
    expect(statusColor('ON_BENCH')).toBe('warning');
    expect(statusColor('PASSED_QC')).toBe('success');
  });
});

describe('formatDate', () => {
  it('shows a timestamp as its local date', () => {
    expect(formatDate('2026-10-14T18:25:00Z')).toBe(new Date('2026-10-14T18:25:00Z').toLocaleDateString());
  });

  it('shows a calendar date as that same day', () => {
    expect(formatDate('2027-03-03')).toBe(new Date(2027, 2, 3).toLocaleDateString());
  });

  it('returns N/A without a date', () => {
    expect(formatDate(null)).toBe('N/A');
    expect(formatDate('')).toBe('N/A');
  });
});

describe('formatEstCompletion and formatEstRange', () => {
  const estimate = { range_start_date: '2027-03-01', estimated_date: '2027-03-03', range_end_date: '2027-03-10' };
  const start = new Date(2027, 2, 1).toLocaleDateString();
  const best = new Date(2027, 2, 3).toLocaleDateString();
  const end = new Date(2027, 2, 10).toLocaleDateString();

  it('shows the best guess and the likely range without shifting the dates a day', () => {
    expect(formatEstRange(estimate)).toBe(`${start} – ${end}`);
    expect(formatEstCompletion(estimate)).toBe(`${best} (likely ${start} – ${end})`);
  });

  it('starts the range at the best guess when there is no early date', () => {
    const { range_start_date, ...noStart } = estimate;
    expect(formatEstRange(noStart)).toBe(`${best} – ${end}`);
  });

  it('shows only the best guess when the range is one day', () => {
    const oneDay = { range_start_date: '2027-03-03', estimated_date: '2027-03-03', range_end_date: '2027-03-03' };
    expect(formatEstRange(oneDay)).toBeNull();
    expect(formatEstCompletion(oneDay)).toBe(best);
  });

  it('returns N/A without an estimate', () => {
    expect(formatEstCompletion(null)).toBe('N/A');
    expect(formatEstRange(null)).toBeNull();
  });
});

describe('formatConfidence', () => {
  it('labels confidence levels', () => {
    expect(formatConfidence('LOW')).toBe('Low');
    expect(formatConfidence('MEDIUM')).toBe('Medium');
    expect(formatConfidence('HIGH')).toBe('High');
    expect(formatConfidence(undefined)).toBe('N/A');
  });
});
