import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { StatusHistoryTimeline } from '../StatusHistoryTimeline';

describe('StatusHistoryTimeline', () => {
  const mockStatusHistory = [
    {
      timestamp: '2025-04-01T10:00:00Z',
      status: 'NEW',
    },
    {
      timestamp: '2025-04-05T14:30:00Z',
      status: 'IN_PROGRESS',
    },
    {
      timestamp: '2025-04-10T09:15:00Z',
      status: 'COMPLETED',
    },
  ];

  // Unsorted history to test sorting
  const mockUnsortedHistory = [
    {
      timestamp: '2025-04-05T14:30:00Z',
      status: 'IN_PROGRESS',
    },
    {
      timestamp: '2025-04-01T10:00:00Z',
      status: 'NEW',
    },
    {
      timestamp: '2025-04-10T09:15:00Z',
      status: 'COMPLETED',
    },
  ];

  it('renders "No status history available" when no history is provided', () => {
    render(<StatusHistoryTimeline statusHistory={[]} />);
    expect(screen.getByText('No status history available.')).toBeInTheDocument();
  });

  it('renders the timeline with status history', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);
    expect(screen.getByText('Status History')).toBeInTheDocument();
    expect(screen.getByText('NEW')).toBeInTheDocument();
    expect(screen.getByText('IN_PROGRESS')).toBeInTheDocument();
    expect(screen.getByText('COMPLETED')).toBeInTheDocument();
  });

  it('renders dates correctly', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);
    expect(screen.getByText('4/1/2025')).toBeInTheDocument();
    expect(screen.getByText('4/5/2025')).toBeInTheDocument();
    expect(screen.getByText('4/10/2025')).toBeInTheDocument();
  });

  it('sorts history chronologically', () => {
    render(<StatusHistoryTimeline statusHistory={mockUnsortedHistory} />);
    const timestamps = screen.getAllByText(/\d+\/\d+\/\d+/).map(el => el.textContent);
    // Dates should be sorted: 4/1/2025, 4/5/2025, 4/10/2025
    expect(timestamps[0]).toBe('4/1/2025');
    expect(timestamps[1]).toBe('4/5/2025');
    expect(timestamps[2]).toBe('4/10/2025');
  });

  it('renders timeline dots with correct colors based on status', () => {
    render(<StatusHistoryTimeline statusHistory={mockStatusHistory} />);

    // Find all timeline items (often listitem role)
    const timelineItems = screen.getAllByRole('listitem');

    // Assuming the order matches mockStatusHistory after sorting (which it does)

    // Check first item (NEW)
    const newItem = timelineItems[0];
    expect(within(newItem).getByText('NEW')).toBeInTheDocument();
    // Reverting to querySelector as getByRole('img') failed.
    // This will trigger lint warnings but is necessary here.
    const newDot = newItem.querySelector('.MuiTimelineDot-root');
    expect(newDot).toHaveClass('MuiTimelineDot-filledPrimary');

    // Check second item (IN_PROGRESS)
    const progressItem = timelineItems[1];
    expect(within(progressItem).getByText('IN_PROGRESS')).toBeInTheDocument();
    const progressDot = progressItem.querySelector('.MuiTimelineDot-root');
    expect(progressDot).toHaveClass('MuiTimelineDot-filledWarning'); // Updated class for MUI v7+

    // Check third item (COMPLETED)
    const completedItem = timelineItems[2];
    expect(within(completedItem).getByText('COMPLETED')).toBeInTheDocument();
    const completedDot = completedItem.querySelector('.MuiTimelineDot-root');
    expect(completedDot).toHaveClass('MuiTimelineDot-filledSuccess'); // Updated class for MUI v7+
  });
});
