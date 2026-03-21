import { useState, useCallback, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiOptions {
  baseUrl?: string;
}

export const useApiClient = (options?: UseApiOptions) => {
  const { token } = useAuth();
  const base = options?.baseUrl || BASE_URL;

  const getHeaders = useCallback((): HeadersInit => ({
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token]);

  const handleResponse = async (res: Response) => {
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Error ${res.status}: ${text}`);
    }
    return res.json();
  };

  const get = useCallback(async <T = any>(endpoint: string): Promise<T> => {
    const res = await fetch(`${base}${endpoint}`, {
      method: "GET",
      headers: getHeaders(),
    });
    return handleResponse(res);
  }, [base, getHeaders]);

  const post = useCallback(async <T = any>(endpoint: string, body: any): Promise<T> => {
    const res = await fetch(`${base}${endpoint}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  }, [base, getHeaders]);

  const put = useCallback(async <T = any>(endpoint: string, body: any): Promise<T> => {
    const res = await fetch(`${base}${endpoint}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  }, [base, getHeaders]);

  const del = useCallback(async <T = any>(endpoint: string): Promise<T> => {
    const res = await fetch(`${base}${endpoint}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    return handleResponse(res);
  }, [base, getHeaders]);

  return { get, post, put, del };
};

export function useGet<T = any>(endpoint: string, autoFetch: boolean = true) {
  const [state, setState] = useState<ApiState<T>>({ data: null, loading: false, error: null });
  const client = useApiClient();
  const mountedRef = useRef(true);

  const fetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await client.get<T>(endpoint);
      if (mountedRef.current) setState({ data, loading: false, error: null });
    } catch (err: any) {
      if (mountedRef.current) setState((prev) => ({ ...prev, loading: false, error: err.message }));
    }
  }, [endpoint, client]);

  useEffect(() => {
    mountedRef.current = true;
    if (autoFetch) fetch();
    return () => { mountedRef.current = false; };
  }, [autoFetch, fetch]);

  return { ...state, refetch: fetch };
}

export function usePost<TReq = any, TRes = any>(endpoint: string) {
  const [state, setState] = useState<ApiState<TRes>>({ data: null, loading: false, error: null });
  const client = useApiClient();

  const execute = useCallback(async (body: TReq) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await client.post<TRes>(endpoint, body);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err: any) {
      setState((prev) => ({ ...prev, loading: false, error: err.message }));
      throw err;
    }
  }, [endpoint, client]);

  return { ...state, execute };
}

export function usePut<TReq = any, TRes = any>(endpoint: string) {
  const [state, setState] = useState<ApiState<TRes>>({ data: null, loading: false, error: null });
  const client = useApiClient();

  const execute = useCallback(async (body: TReq) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await client.put<TRes>(endpoint, body);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err: any) {
      setState((prev) => ({ ...prev, loading: false, error: err.message }));
      throw err;
    }
  }, [endpoint, client]);

  return { ...state, execute };
}
