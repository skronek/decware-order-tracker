import { formatStatus, statusColor, isFinished, formatEstCompletion, formatConfidence } from '../orderFormat';

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

describe('formatEstCompletion', () => {
  it('shows a range of calendar dates without shifting them a day', () => {
    const start = new Date(2027, 2, 3).toLocaleDateString();
    const end = new Date(2027, 2, 10).toLocaleDateString();
    expect(formatEstCompletion({ estimated_date: '2027-03-03', range_end_date: '2027-03-10' }))
      .toBe(`${start} – ${end}`);
  });

  it('shows a single date when the range is one day', () => {
    expect(formatEstCompletion({ estimated_date: '2027-03-03', range_end_date: '2027-03-03' }))
      .toBe(new Date(2027, 2, 3).toLocaleDateString());
  });

  it('returns N/A without an estimate', () => {
    expect(formatEstCompletion(null)).toBe('N/A');
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
