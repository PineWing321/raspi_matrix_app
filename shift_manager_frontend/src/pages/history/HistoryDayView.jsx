import { useState, useEffect } from "react";
import "./HistoryDayView.css";

export default function HistoryDayView() {
  const [selectedDate, setSelectedDate] = useState('');
  const [shifts, setShifts] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!selectedDate) return;

    const fetchData = async () => {
      try {
        const res = await fetch(`/api/history?date=${selectedDate}`);
        if (!res.ok) throw new Error("Failed to fetch data");
        const data = await res.json();

        setShifts(data.shifts || []);
        setSummary(data.summary || null);
      } catch (err) {
        console.error("Fetch error:", err);
        setShifts([]);
        setSummary(null);
      }
    };

    fetchData();
  }, [selectedDate]);

  return (
    <div className="day-view-container">
      {/* Top bar for selecting a date */}
      <div className="date-selector">
        <label htmlFor="day-input">Select a Date:</label>
        <input
          type="date"
          id="day-input"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
      </div>

      {/* Bottom section split in half */}
      <div className="day-view-content">
        <div className="shift-list">
          <h3>Shifts for Selected Day</h3>
          {shifts.length > 0 ? (
            <ul>
              {shifts.map((shift) => (
                <li key={shift.id} className="shift-row">
                  <strong>{shift.name}</strong><br />
                  {shift.start} – {shift.end}
                </li>
              ))}
            </ul>
          ) : (
            <p>No shift data available.</p>
          )}
        </div>

        <div className="day-summary">
          <h3>Daily Summary</h3>
          {summary ? (
            <ul>
              <li><strong>Average OEE:</strong> <span className="stat green">{summary.averageOEE}%</span></li>
              <li><strong>Total Runtime:</strong> <span className="stat blue">{summary.totalRuntime}</span></li>
              <li><strong>Total Stops:</strong> {summary.totalStops}</li>
            </ul>
          ) : (
            selectedDate ? <p>Loading summary...</p> : <p>Select a date to view summary.</p>
          )}
        </div>
      </div>
    </div>
  );
}

