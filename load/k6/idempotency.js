import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";
import { BASE_URL, getVuToken, jsonHeaders } from "./helpers.js";

const errorRate = new Rate("business_error_rate");
const unexpected5xx = new Rate("unexpected_5xx");
const replayRate = new Rate("idempotency_replay_rate");
const duplicateSideEffects = new Counter("duplicate_side_effects");
const writeDuration = new Trend("write_duration", true);

export const options = {
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
  scenarios: {
    idempotent_writes: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.WRITE_RPS || 2),
      timeUnit: "1s",
      duration: __ENV.DURATION || "30s",
      preAllocatedVUs: 5,
      maxVUs: 20,
      exec: "idempotentWrite",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    business_error_rate: ["rate<0.01"],
    unexpected_5xx: ["rate==0"],
    duplicate_side_effects: ["count==0"],
    write_duration: ["p(95)<8000"],
  },
};

function is5xx(res) {
  return Boolean(res && res.status >= 500);
}

function businessCode(res) {
  try {
    return res.json("code");
  } catch (err) {
    return null;
  }
}

export function idempotentWrite() {
  const token = getVuToken();
  if (!token) {
    errorRate.add(true);
    return;
  }
  const nodeCode = `K6${__VU}I${__ITER}${String(Date.now()).slice(-5)}`.slice(0, 16);
  const payload = JSON.stringify({
    node_code: nodeCode,
    name: `k6-node-${nodeCode}`,
    location: "load-test",
    latitude: 30.5,
    longitude: 114.3,
    capacity: 500.0,
  });
  const idemKey = `idem-${nodeCode}`;
  const headers = jsonHeaders(token, { "X-Idempotency-Key": idemKey });

  const first = http.post(`${BASE_URL}/api/nodes/storage-centers`, payload, {
    headers,
    tags: { name: "write" },
  });
  writeDuration.add(first.timings.duration);
  unexpected5xx.add(is5xx(first));

  const replay = http.post(`${BASE_URL}/api/nodes/storage-centers`, payload, {
    headers,
    tags: { name: "write" },
  });
  writeDuration.add(replay.timings.duration);
  unexpected5xx.add(is5xx(replay));

  const firstOk = first.status === 200 && businessCode(first) === 0;
  const replaySame = replay.status === first.status && replay.body === first.body;
  replayRate.add(firstOk && replaySame);
  const sequentialOk = check(first, {
    "idempotent write succeeded": () => firstOk,
    "replay matches original": () => replaySame,
  });

  const concurrent = http.batch([
    ["POST", `${BASE_URL}/api/nodes/storage-centers`, payload, { headers, tags: { name: "write" } }],
    ["POST", `${BASE_URL}/api/nodes/storage-centers`, payload, { headers, tags: { name: "write" } }],
    ["POST", `${BASE_URL}/api/nodes/storage-centers`, payload, { headers, tags: { name: "write" } }],
  ]);
  let createdCodes = {};
  let concurrentUnexpected = false;
  concurrent.forEach((res) => {
    unexpected5xx.add(is5xx(res));
    writeDuration.add(res.timings.duration);
    const code = businessCode(res);
    if (res.status >= 500 || (res.status === 200 && code !== 0 && code !== 40902)) {
      concurrentUnexpected = true;
    }
    if (res.status === 200 && code === 0) {
      try {
        createdCodes[res.json("data.node_code") || nodeCode] = true;
      } catch (err) {
        createdCodes[nodeCode] = true;
      }
    }
  });
  if (Object.keys(createdCodes).length > 1) {
    duplicateSideEffects.add(1);
  }

  const concurrentOk = !concurrentUnexpected && Object.keys(createdCodes).length <= 1;
  errorRate.add(!(sequentialOk && firstOk && replaySame && concurrentOk));
  sleep(0.05);
}
