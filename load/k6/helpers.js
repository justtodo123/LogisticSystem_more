export function header(name, fallback) {
  const value = __ENV[name];
  return value && value.length > 0 ? value : fallback;
}

export const BASE_URL = header("BASE_URL", "http://127.0.0.1:18001").replace(/\/$/, "");
export const USERNAME = header("LOAD_USERNAME", "admin");
export const PASSWORD = header("LOAD_PASSWORD", "123456");

export function jsonHeaders(token, extra) {
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "X-Request-ID": `k6-${__VU}-${__ITER}-${Date.now()}`,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return Object.assign(headers, extra || {});
}
