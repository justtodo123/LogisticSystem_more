import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";
import { BASE_URL, PASSWORD, USERNAME, jsonHeaders } from "./helpers.js";

const errorRate = new Rate("business_error_rate");

export const options = {
  scenarios: {
    spike: {
      executor: "ramping-arrival-rate",
      startRate: Number(__ENV.START_RPS || 2),
      timeUnit: "1s",
      preAllocatedVUs: 30,
      maxVUs: 80,
      stages: [
        { duration: "1m", target: Number(__ENV.WARM_RPS || 5) },
        { duration: "30s", target: Number(__ENV.SPIKE_RPS || 25) },
        { duration: "2m", target: Number(__ENV.SPIKE_RPS || 25) },
        { duration: "30s", target: Number(__ENV.WARM_RPS || 5) },
        { duration: "1m", target: Number(__ENV.WARM_RPS || 5) },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    business_error_rate: ["rate<0.01"],
    http_req_duration: ["p(95)<3000"],
  },
};

export default function () {
  const health = http.get(`${BASE_URL}/api/health`, { headers: jsonHeaders() });
  const login = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: USERNAME, password: PASSWORD }),
    { headers: jsonHeaders() },
  );
  let ok = health.status === 200 && login.status === 200;
  try {
    ok = ok && login.json("code") === 0;
  } catch (err) {
    ok = false;
  }
  if (ok) {
    const token = login.json("data.access_token");
    const me = http.get(`${BASE_URL}/api/auth/me`, { headers: jsonHeaders(token) });
    ok = me.status === 200 && me.json("code") === 0;
  }
  check(health, { "health 200": (r) => r.status === 200 });
  errorRate.add(!ok);
  sleep(0.05);
}
