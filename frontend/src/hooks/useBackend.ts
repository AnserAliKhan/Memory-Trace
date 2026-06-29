import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'refound_backend_url';
const DEFAULT_URL = 'http://localhost:8000';

export function useBackend() {
  const [backendUrl, setBackendUrl] = useState<string>(() => {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_URL;
  });

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // The ping function – tests if the backend is reachable
  const ping = useCallback(async (url: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${url}/api/health`, {
        signal: AbortSignal.timeout(3000), // 3-second timeout
      });
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          setIsConnected(true);
          return true;
        }
      }
      setIsConnected(false);
      return false;
    } catch (err) {
      setIsConnected(false);
      setError(err instanceof Error ? err.message : 'Connection failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Change the URL and persist it
  const setUrl = useCallback((url: string) => {
    setBackendUrl(url);
    localStorage.setItem(STORAGE_KEY, url);
  }, []);

  // Connect: set the URL, ping it, and return success/failure
  const connect = useCallback(async (url: string): Promise<boolean> => {
    setUrl(url);
    const success = await ping(url);
    return success;
  }, [setUrl, ping]);

  // On mount: load the stored URL and ping it automatically
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setBackendUrl(stored);
      ping(stored);
    } else {
      // If no stored URL, try the default
      ping(DEFAULT_URL);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount

  return {
    backendUrl,
    setBackendUrl: setUrl,
    isConnected,
    isLoading,
    error,
    ping,
    connect,
  };
}