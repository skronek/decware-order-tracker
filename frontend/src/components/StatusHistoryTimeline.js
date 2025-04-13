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

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const utcDate = new Date(date.getTime() + date.getTimezoneOffset() * 60000);
  return `${utcDate.getMonth() + 1}/${utcDate.getDate()}/${utcDate.getFullYear()}`;
};

export const StatusHistoryTimeline = ({ statusHistory }) => {
  if (!statusHistory || statusHistory.length === 0) {
    return <Typography>No status history available.</Typography>;
  }

  // Sort history chronologically if not already sorted
  const sortedHistory = [...statusHistory].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Status History
      </Typography>
      <Timeline position="alternate">
        {sortedHistory.map((item, index) => (
          <TimelineItem key={index}>
            <TimelineOppositeContent color="text.secondary">
              {formatDate(item.timestamp)}
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot
                color={
                  item.status === 'NEW'
                    ? 'primary'
                    : item.status === 'IN_PROGRESS'
                    ? 'warning'
                    : 'success'
                }
              />
              {index < sortedHistory.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>{item.status}</TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Paper>
  );
};
