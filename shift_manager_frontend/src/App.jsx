import { Routes, Route } from 'react-router-dom';
import ShiftManager from './shiftManager';
import EditShift from "./pages/EditShift.jsx";
import HistoryMain from './pages/history/HistoryMain.jsx';
import HistoryDayView from './pages/history/HistoryDayView.jsx';
import HistoryRangeView from './pages/history/HistoryRangeView.jsx';

function App() {
  return (
    <Routes>
      {/* Main entry renders the history main menu for now */}
      <Route path="/" element={<HistoryMain />} />

      {/* Shift Manager (if needed later) */}
      <Route path="/manager" element={<ShiftManager />} />

      {/* History navigation */}
      <Route path="/history" element={<HistoryMain />} />
      <Route path="/history/day" element={<HistoryDayView />} />
      <Route path="/history/range" element={<HistoryRangeView />} />
    </Routes>
  );
}

export default App;
