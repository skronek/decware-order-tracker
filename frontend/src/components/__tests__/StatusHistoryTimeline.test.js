import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { StatusHistoryTimeline } from '../StatusHistoryTimeline';

const day = (iso) => new Date(iso).toLocaleDateString();

describe('StatusHistoryTimeline', () => {
  // Rows as the API returns them: newest first
  const mockStatusHistory = [
    { id: 3, previous_status: 'ON_BENCH', new_status: 'PASSED_QC', timestamp: '2025-04-10T15:00:00Z', is_observed: true },
    { id: 2, previous_status: 'NEW', new_status: 'ON_BENCH', timestamp: '2025-04-05T15:00:00Z', is_observed: true },
    { id: 1, previous_status: null, new_status: 'NEW', timestamp: '2025-04-01T15:00:00Z', is_observed: false },
  ];

  it('renders "No status history available" when no history is provided', () => {
    render(<StatusHistoryTimeline statusHistory={[]} />);
    expect(screen.getByText('No status history available.')).toBeInTheDocument();
  });

  it('renders each status with its label, oldest first', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);
    expect(screen.getByText('Status History')).toBeInTheDocument();

    const items = screen.getAllByRole('listitem');
    expect(within(items[0]).getByText('New')).toBeInTheDocument();
    expect(within(items[1]).getByText('On Bench')).toBeInTheDocument();
    expect(within(items[2]).getByText('Passed QC')).toBeInTheDocument();
  });

  it('shows exact dates for observed changes and "First seen" for the rest', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent(`First seen ${day('2025-04-01T15:00:00Z')}`);
    expect(items[1]).toHaveTextContent(day('2025-04-05T15:00:00Z'));
    expect(items[1]).not.toHaveTextContent('First seen');
    expect(items[2]).toHaveTextContent(day('2025-04-10T15:00:00Z'));
  });

  it('colors timeline dots by stage', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);
    const dots = screen.getAllByTestId('timeline-dot');
    expect(dots[0]).toHaveClass('MuiTimelineDot-filledPrimary');
    expect(dots[1]).toHaveClass('MuiTimelineDot-filledWarning');
    expect(dots[2]).toHaveClass('MuiTimelineDot-filledSuccess');
  });
});
