import { useEffect, useState } from "react";

export const useCognition = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/internal/ai/status");
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      console.error("Cognition fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return { status, loading };
};