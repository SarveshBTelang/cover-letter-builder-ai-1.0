const API_BASE = "http://localhost:8000";

export async function fetchDefaults() {
  const res = await fetch(`${API_BASE}/defaults`);
  if (!res.ok) throw new Error("Failed to fetch defaults");
  return res.json();
}

export async function generatePdf(payload) {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Generate failed: ${res.status} ${text}`);
  }

  const filename = getFilenameFromResponse(res) || "output.pdf";
  const blob = await res.blob();

  return { blob, filename };
}

export async function downloadDocx() {
  const res = await fetch(`${API_BASE}/download/docx`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DOCX download failed: ${res.status} ${text}`);
  }

  const blob = await res.blob();
  return { blob, filename: getFilenameFromResponse(res) || "main.docx" };
}

function getFilenameFromResponse(res) {
  const cd = res.headers.get("content-disposition");
  if (!cd) return null;
  const match = cd.match(/filename="?([^"]+)"?/);
  return match ? match[1] : null;
}