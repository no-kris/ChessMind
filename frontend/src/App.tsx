import { Chessboard } from "react-chessboard";

function App() {
  async function handleAnalyze() {
    const res = await fetch("/api/analyze");
    const data = await res.json();
    alert(data.message);
  }

  return (
    <div className="app-layout">
      <main className="board-area">
        <Chessboard />
      </main>
      <aside className="coach-panel">
        <h2>Coach</h2>
        <p>No analysis yet.</p>
        <div>
          <button onClick={handleAnalyze}>Analyze</button>
        </div>
      </aside>
    </div>
  );
}
export default App;
