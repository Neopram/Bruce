import { useEffect, useState } from "react";

export const useEmotion = () => {
  const [emotion, setEmotion] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchEmotion = async () => {
    try {
      const res = await fetch("/internal/emotion/state");
      const data = await res.json();
      setEmotion(data);
    } catch (e) {
      console.error("Emotion fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmotion();
    const interval = setInterval(fetchEmotion, 30000);
    return () => clearInterval(interval);
  }, []);

  return { emotion, loading };
};