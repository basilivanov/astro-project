// ############################################################################
// AI_HEADER: MODULE_COPY_BUTTON
// ROLE: Client-side copy button for text blocks.
// DEPENDENCIES: React.
// GRACE_ANCHORS: [COPY_BUTTON]
// ############################################################################

"use client";

import { useRef, useState } from "react";

type CopyStatus = "idle" | "copied" | "error";

type CopyButtonProps = {
  text: string;
  label?: string;
  className?: string;
  disabled?: boolean;
};

// #START_BLOCK_COPY_BUTTON
export default function CopyButton({
  text,
  label = "Копировать",
  className = "btn btn-secondary",
  disabled = false,
}: CopyButtonProps) {
  const [status, setStatus] = useState<CopyStatus>("idle");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetStatus = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => setStatus("idle"), 2000);
  };

  const handleCopy = async () => {
    if (disabled || !text) return;
    try {
      await navigator.clipboard.writeText(text);
      setStatus("copied");
      resetStatus();
      return;
    } catch {
      // Fallback to document.execCommand for older browsers.
    }

    try {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setStatus("copied");
      resetStatus();
    } catch {
      setStatus("error");
      resetStatus();
    }
  };

  const labelText =
    status === "copied"
      ? "Скопировано"
      : status === "error"
      ? "Не скопировано"
      : label;

  return (
    <button
      type="button"
      className={className}
      onClick={handleCopy}
      disabled={disabled}
    >
      {labelText}
    </button>
  );
}
// #END_BLOCK_COPY_BUTTON
