import React from 'react';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import { Typography, Paper } from '@mui/material';
import { formatStatus, statusColor } from '../utils/orderFormat';

// Unobserved rows (an order's first status, or a change spotted after missed scraper
// runs) weren't timestamped when the change happened, only when it was first noticed
const formatWhen = (item) => {
  const date = new Date(item.timestamp).toLocaleDateString();
  return item.is_observed === false ? `First seen ${date}` : date;
};

export const StatusHistoryTimeline = ({ statusHistory }) => {
  if (!statusHistory || statusHistory.length === 0) {
    return <Typography>No status history available.</Typography>;
  }

  // The API returns newest first; show the order's progress oldest first
  const sortedHistory = [...statusHistory].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );

  return (
    <Paper sx={{ p: 3, mt: 3 }} data-testid="status-history-timeline">
      <Typography variant="h6" gutterBottom>
        Status History
      </Typography>
      <Timeline position="alternate">
        {sortedHistory.map((item, index) => (
          <TimelineItem key={item.id ?? index}>
            <TimelineOppositeContent color="text.secondary">
              {formatWhen(item)}
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot color={statusColor(item.new_status)} />
              {index < sortedHistory.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>{formatStatus(item.new_status)}</TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Paper>
  );
};
