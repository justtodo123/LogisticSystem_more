import http from "k6/http";

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
    "X-Request-ID": `k6-${Date.now()}-${Math.floor(Math.random() * 1e9)}`,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return Object.assign(headers, extra || {});
}

export function login() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: USERNAME, password: PASSWORD }),
    { headers: jsonHeaders(), tags: { name: "login" } },
  );
  let token = null;
  let ok = res.status === 200;
  try {
    ok = ok && res.json("code") === 0;
    if (ok) {
      token = res.json("data.access_token");
    }
  } catch (err) {
    ok = false;
  }
  return { res, token, ok };
}
