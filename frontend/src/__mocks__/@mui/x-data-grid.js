import React from 'react';

export const DataGrid = ({ rows, columns }) => (
  <div data-testid="data-grid">
    <table>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.field}>{col.headerName}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            {columns.map((col) => (
              <td key={`${row.id}-${col.field}`}>
                {row[col.field]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
