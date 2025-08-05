// src/pages/history/HistoryDayView.jsx
import './HistoryDayView.css'; // We'll define this next

export default function HistoryDayView() {
  // Dummy placeholder data
  const shifts = [
    { id: 1, name: "Shift A", start: "08:00", stop: "16:00" },
    { id: 2, name: "Shift B", start: "16:00", stop: "00:00" },
  ];

  const summary = {
    availability: 92.3,
    oee: 87.1,
  };

  return (
    <div className="day-view-container">
      <div className="shift-list">
        <h3>Shifts for the Day</h3>
        {shifts.map((shift) => (
          <div key={shift.id} className="shift-card">
            <h4>{shift.name}</h4>
            <p><strong>Start:</strong> {shift.start}</p>
            <p><strong>Stop:</strong> {shift.stop}</p>
          </div>
        ))}
      </div>

      <div className="day-summary">
        <h3>Daily Summary</h3>
        <p><strong>Availability:</strong> <span className="stat green">{summary.availability}%</span></p>
        <p><strong>OEE:</strong> <span className="stat blue">{summary.oee}%</span></p>
      </div>
    </div>
  );
}

