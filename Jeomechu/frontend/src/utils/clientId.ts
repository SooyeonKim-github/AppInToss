const STORAGE_KEY = "jeomechu_client_id";

export function getClientId(): string {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored) return stored;

  const id = crypto.randomUUID();
  window.localStorage.setItem(STORAGE_KEY, id);
  return id;
}
