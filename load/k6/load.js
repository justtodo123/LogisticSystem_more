import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";
import { BASE_URL, jsonHeaders, login } from "./helpers.js";

const errorRate = new Rate("business_error_rate");

export const options = {
  scenarios: {
    reads: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RPS || 8),
      timeUnit: "1s",
      duration: __ENV.DURATION || "5m",
      preAllocatedVUs: 20,
      maxVUs: 60,
      exec: "readMix",
    },
    auth: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.LOGIN_RPS || 1),
      timeUnit: "1s",
      duration: __ENV.DURATION || "5m",
      preAllocatedVUs: 2,
      maxVUs: 10,
      exec: "loginMix",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    business_error_rate: ["rate<0.01"],
    dropped_iterations: ["count<100"],
    http_req_duration: ["p(95)<5000"],
  },
};

export function setup() {
  const result = login();
  if (!result.ok || !result.token) {
    throw new Error("setup login failed");
  }
  return { token: result.token };
}

export function readMix(data) {
  const health = http.get(`${BASE_URL}/api/health`, {
    headers: jsonHeaders(),
    tags: { name: "health" },
  });
  check(health, {
    "health 200": (r) => r.status === 200,
    "health echoes request id": (r) => Boolean(r.headers["X-Request-Id"] || r.headers["X-Request-ID"]),
  });

  const token = data && data.token;
  if (!token) {
    errorRate.add(true);
    return;
  }

  const me = http.get(`${BASE_URL}/api/auth/me`, {
    headers: jsonHeaders(token),
    tags: { name: "me" },
  });
  const orders = http.get(`${BASE_URL}/api/orders?page=1&page_size=20`, {
    headers: jsonHeaders(token),
    tags: { name: "orders" },
  });
  const meOk = check(me, { "me 200": (r) => r.status === 200 && r.json("code") === 0 });
  const ordersOk = check(orders, {
    "orders 200": (r) => r.status === 200 && r.json("code") === 0,
  });
  errorRate.add(!(meOk && ordersOk));

  const metrics = http.get(`${BASE_URL}/metrics`, {
    headers: jsonHeaders(),
    tags: { name: "metrics" },
  });
  check(metrics, { "metrics 200": (r) => r.status === 200 });
  sleep(0.1);
}

export function loginMix() {
  const result = login();
  check(result.res, {
    "login status 200": (r) => r.status === 200,
    "login business 0": () => result.ok,
  });
  errorRate.add(!result.ok);
  sleep(0.05);
}
