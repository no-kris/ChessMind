import { Chessboard } from "react-chessboard";

function App() {
  return (
    <div className="app-layout">
      <main className="board-area">
        <Chessboard />
      </main>
      <aside className="coach-panel">
        <h2>Coach</h2>
        <p>No analysis yet.</p>
      </aside>
    </div>
  );
}
export default App;
