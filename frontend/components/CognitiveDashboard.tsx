
import { useState } from "react";

export default function CognitiveDashboard() {
  const [editableFiles, setEditableFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [diffResult, setDiffResult] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [superuser, setSuperuser] = useState(false);

  const fetchDiff = async () => {
    if (!selectedFile || !superuser) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/api/self-rewrite?file=${selectedFile}&simulate=true`);
      const data = await res.json();
      setDiffResult(data.diff || "No changes proposed.");
    } catch (err) {
      setDiffResult("Error contacting backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadFileList = () => {
    // Hardcoded list for now, could be dynamically fetched later
    setEditableFiles(["meta_agent_trainer.py", "memory.py", "orchestrator.py"]);
  };

  return (
    <div className="p-4 rounded-xl shadow-xl bg-gray-950 text-white">
      <h2 className="text-xl font-bold mb-2">🧠 Self-Evolution Panel</h2>
      <label className="block mb-2">
        <input
          type="checkbox"
          checked={superuser}
          onChange={(e) => setSuperuser(e.target.checked)}
          className="mr-2"
        />
        Grant Superuser Access
      </label>
      <button
        onClick={loadFileList}
        className="px-4 py-2 bg-blue-700 rounded hover:bg-blue-800 mb-4"
      >
        Load Editable Files
      </button>
      <select
        value={selectedFile}
        onChange={(e) => setSelectedFile(e.target.value)}
        className="block mb-4 w-full text-black p-2"
      >
        <option value="">Select file...</option>
        {editableFiles.map((file) => (
          <option key={file} value={file}>
            {file}
          </option>
        ))}
      </select>
      <button
        onClick={fetchDiff}
        disabled={!selectedFile || !superuser}
        className="px-4 py-2 bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
      >
        Simulate Self-Rewrite
      </button>
      {isLoading && <p className="mt-4 text-yellow-400">Simulating rewrite...</p>}
      {diffResult && (
        <pre className="mt-4 p-2 bg-black border border-gray-700 overflow-auto text-xs whitespace-pre-wrap max-h-96">
          {diffResult}
        </pre>
      )}
    </div>
  );
}
