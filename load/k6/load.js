import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";
import { BASE_URL, PASSWORD, USERNAME, jsonHeaders } from "./helpers.js";

const errorRate = new Rate("business_error_rate");

export const options = {
  scenarios: {
    load: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RPS || 8),
      timeUnit: "1s",
      duration: __ENV.DURATION || "5m",
      preAllocatedVUs: 20,
      maxVUs: 60,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    business_error_rate: ["rate<0.01"],
    http_req_duration: ["p(95)<2000"],
  },
};

function login() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: USERNAME, password: PASSWORD }),
    { headers: jsonHeaders() },
  );
  const ok = check(res, {
    "login status 200": (r) => r.status === 200,
    "login business 0": (r) => {
      try {
        return r.json("code") === 0;
      } catch (err) {
        return false;
      }
    },
  });
  errorRate.add(!ok);
  if (!ok) {
    return null;
  }
  return res.json("data.access_token");
}

export default function () {
  const health = http.get(`${BASE_URL}/api/health`, { headers: jsonHeaders() });
  check(health, {
    "health 200": (r) => r.status === 200,
    "health echoes request id": (r) => Boolean(r.headers["X-Request-Id"] || r.headers["X-Request-ID"]),
  });

  const token = login();
  if (token) {
    const me = http.get(`${BASE_URL}/api/auth/me`, { headers: jsonHeaders(token) });
    const orders = http.get(`${BASE_URL}/api/orders?page=1&page_size=20`, {
      headers: jsonHeaders(token),
    });
    const meOk = check(me, { "me 200": (r) => r.status === 200 && r.json("code") === 0 });
    const ordersOk = check(orders, {
      "orders 200": (r) => r.status === 200 && r.json("code") === 0,
    });
    errorRate.add(!(meOk && ordersOk));
  }

  const metrics = http.get(`${BASE_URL}/metrics`, { headers: jsonHeaders() });
  check(metrics, { "metrics 200": (r) => r.status === 200 });
  sleep(0.1);
}
