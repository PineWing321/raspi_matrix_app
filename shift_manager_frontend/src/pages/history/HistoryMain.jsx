import { useNavigate } from 'react-router-dom';
import './HistoryMain.css';

export default function HistoryMain() {
  const navigate = useNavigate();

  return (
    <div className="history-main">
      <h2>Shift History</h2>
      <div className="button-grid">
        <button onClick={() => navigate('/history/day')}>View Shifts for Day</button>
        <button onClick={() => navigate('/history/range')}>View Range of Days</button>
      </div>
    </div>
  );
}
