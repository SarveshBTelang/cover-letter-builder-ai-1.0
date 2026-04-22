import React from "react";

export default function FormField({
  label,
  name,
  value,
  onChange,
  type = "text",
  isDefault,
}) {
  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      onChange({
        target: { name, value: text },
      });
    } catch (err) {
      console.error("Clipboard error:", err);
    }
  };

  return (
    <div className="form-row">
      <label className="form-label">{label}</label>

      <div className="input-wrapper">
        <input
          className={`rect-input ${isDefault ? "default-input" : ""}`}
          name={name}
          value={value || ""}
          onChange={onChange}
          type={type}
        />

        <button type="button" className="paste-btn" onClick={handlePaste}>
          Paste
        </button>

        <button type="button" className="clear-btn" onClick={handleClear}>
          Clear
        </button>
      </div>
    </div>
  );
}