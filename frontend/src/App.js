import React, { useEffect, useState, useRef } from "react";
import FormField from "./components/FormField";
import { fetchDefaults, generatePdf, downloadDocx } from "./api";

export default function App() {
  const [defaults, setDefaults] = useState({});
  const [form, setForm] = useState({});
  const [touched, setTouched] = useState({});

  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingDocx, setLoadingDocx] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  const [logs, setLogs] = useState([]);
  const wsRef = useRef(null);
  const logEndRef = useRef(null);

  useEffect(() => {
    loadDefaults();
    connectWebSocket();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // =========================
  // 🔥 WebSocket (PROD SAFE)
  // =========================
  function connectWebSocket() {
    const WS_BASE =
      window.location.hostname === "localhost"
        ? "ws://localhost:8000"
        : "wss://cover-letter-builder-ai-1-0.onrender.com";

    const wsUrl = `${WS_BASE}/ws/logs`;

    // Prevent multiple connections (VERY IMPORTANT for React StrictMode)
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("✅ WebSocket connected:", wsUrl);
    };

    ws.onmessage = (event) => {
      setLogs((prev) => [...prev, event.data]);
    };

    ws.onerror = (err) => {
      console.error("❌ WebSocket error:", err);
    };

    ws.onclose = () => {
      console.warn("⚠️ WebSocket closed. Reconnecting in 3s...");

      wsRef.current = null;

      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    wsRef.current = ws;
  }

  // =========================
  // Load defaults
  // =========================
  async function loadDefaults() {
    try {
      const data = await fetchDefaults();
      setDefaults(data);
      setForm(data);
      setTouched({});
    } catch (err) {
      setError(err.message);
    }
  }

  function handleChange(e) {
    const { name, value } = e.target;

    setForm((prev) => ({ ...prev, [name]: value }));
    setTouched((prev) => ({ ...prev, [name]: true }));
  }

  async function handleGenerate(e) {
    e.preventDefault();
    setError(null);
    setDone(false);
    setLogs([]);
    setLoadingPdf(true);

    try {
      const { blob, filename } = await generatePdf(form);
      downloadBlob(blob, filename);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingPdf(false);
    }
  }

  async function handleDownloadDocx() {
    setError(null);
    setDone(false);
    setLoadingDocx(true);

    try {
      const { blob, filename } = await downloadDocx();
      downloadBlob(blob, filename);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingDocx(false);
    }
  }

  function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  const fields = [
    { key: "ACCESS_KEY", label: "Access Key" },
    { key: "FIRM", label: "Firm" },
    { key: "LOCATION", label: "Location" },
    { key: "POSITION", label: "Position" },
    { key: "JOB_DESCRIPTION", label: "Job Description" },
    { key: "GREETING", label: "Greeting" },
    { key: "BODY_WORD_COUNT", label: "Body Word Count" },
    { key: "TIMEZONE", label: "Timezone" },
    { key: "OUTPUT_FILE_NAME", label: "Output File Name" },
    { key: "TEMPLATE_PATH", label: "Template Path" },
    { key: "LIBREOFFICE_PATH", label: "LibreOffice Path" },
  ];

  return (
    <div className="app-layout">

      {/* LEFT PANEL */}
      <div className="container">
        <h1 className="title">Cover Letter Builder AI 1.0</h1>

        <h4 className="subtitle">
          ▸ Automated Cover Letter Generation using LLMs in docx and pdf format  
          <br />
          ▸ Sync and update LLM context files via Cloud storage
        </h4>

        <h5 className="author" style={{ fontWeight: 300, fontStyle: "italic" }}>
          Author: Sarvesh Telang
        </h5>

        {error && <div className="error">{error}</div>}

        <form className="form" onSubmit={handleGenerate}>
          {fields.map((f) => (
            <FormField
              key={f.key}
              label={f.label}
              name={f.key}
              value={form[f.key] ?? ""}
              onChange={handleChange}
              isDefault={!touched[f.key]}
            />
          ))}

          <div className="button-row">
            <button className="btn btn-green" disabled={loadingPdf}>
              {loadingPdf ? "Generating..." : "Generate PDF"}
            </button>

            <button
              type="button"
              className="btn btn-blue"
              onClick={handleDownloadDocx}
              disabled={loadingDocx}
            >
              Download DOCX
            </button>
          </div>
        </form>

        {done && <div className="done">Done !!!</div>}

        <div className="note" style={{ marginTop: "40px" }}>
          <strong>Defaults loaded:</strong>{" "}
          {Object.keys(defaults).length ? "Yes" : "No"}
        </div>
      </div>

      {/* RIGHT TERMINAL */}
      <div className="terminal">
        <h3>🖥 Backend Logs</h3>

        {logs.map((log, i) => (
          <pre key={i}>{log}</pre>
        ))}

        <div ref={logEndRef} />
      </div>
    </div>
  );
}