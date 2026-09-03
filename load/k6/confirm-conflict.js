import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";
import { BASE_URL, getVuToken, jsonHeaders, newRequestId } from "./helpers.js";

const errorRate = new Rate("business_error_rate");
const unexpected5xx = new Rate("unexpected_5xx");
const conflictRate = new Rate("confirmation_conflict_rate");
const successCount = new Counter("confirmation_success_total");
const successRate = new Rate("confirmation_success_rate");
const duplicateSideEffects = new Counter("duplicate_side_effects");
const confirmDuration = new Trend("confirm_duration", true);

export const options = {
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
  scenarios: {
    confirm: {
      executor: "shared-iterations",
      vus: Number(__ENV.CONFIRM_VUS || 8),
      iterations: Number(__ENV.CONFIRM_VUS || 8),
      maxDuration: __ENV.DURATION || "1m",
      exec: "confirmSame",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    business_error_rate: ["rate==0"],
    unexpected_5xx: ["rate==0"],
    duplicate_side_effects: ["count==0"],
    confirmation_success_total: ["count==1"],
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

export function setup() {
  const token = getVuToken();
  if (!token) {
    throw new Error("setup login failed");
  }
  const create = http.post(
    `${BASE_URL}/api/schedule/global`,
    JSON.stringify({ algorithm: "traditional", preview: true }),
    {
      headers: jsonHeaders(token, { "X-Idempotency-Key": `sched-${newRequestId()}` }),
      tags: { name: "write" },
    },
  );
  if (create.status !== 200 || businessCode(create) !== 0) {
    throw new Error(`setup schedule create failed: ${create.status} ${create.body}`);
  }
  const scheduleCode = create.json("data.schedule_code");
  if (!scheduleCode) {
    throw new Error("setup schedule_code missing");
  }
  console.log(`write_path_schedule_code=${scheduleCode}`);
  return { scheduleCode };
}

export function confirmSame(data) {
  const token = getVuToken();
  if (!token) {
    errorRate.add(true);
    return;
  }
  const headers = jsonHeaders(token, {
    "X-Idempotency-Key": `confirm-${__VU}-${__ITER}-${newRequestId()}`,
  });
  const res = http.post(`${BASE_URL}/api/schedule/confirm/${data.scheduleCode}`, null, {
    headers,
    tags: { name: "confirm" },
    responseCallback: http.expectedStatuses(200, 409),
  });
  confirmDuration.add(res.timings.duration);
  unexpected5xx.add(is5xx(res));
  const code = businessCode(res);
  const success = res.status === 200 && code === 0;
  const conflict = res.status === 409 && code === 40901;
  successRate.add(success);
  conflictRate.add(conflict);
  if (success) {
    successCount.add(1);
  }
  const expected = success || conflict;
  if (!expected) {
    errorRate.add(true);
  } else {
    errorRate.add(false);
  }
  check(res, {
    "confirm is success or conflict": () => expected,
  });
  sleep(0.01);
}

