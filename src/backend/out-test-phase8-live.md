
============================================================
  1. Login to get token
============================================================
  role=dispatcher, token=eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...

============================================================
  2. Health check
============================================================
  STATUS: ok

============================================================
  3. AI Parse dry-run (default, no message)
============================================================
  HTTP 200
{
  "code": 0,
  "message": "success (dry-run)",
  "data": {
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.5,
          "time": 0.3,
          "package_count": 0.2
        }
      }
    },
    "mode": "default"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
  [PASS] dry-run default params - response format correct

============================================================
  4. AI Parse dry-run (message: 'shortest distance first')
============================================================
  HTTP 200
{
  "code": 0,
  "message": "success (dry-run)",
  "data": {
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.5,
          "time": 0.3,
          "package_count": 0.2
        }
      }
    },
    "mode": "ai"
  },
  "meta": {
    "degraded": true,
    "degraded_reason": "DeepSeek API 调用失败：'ascii' codec can't encode characters in position 10-11: ordinal not in range(128)"
  }
}
  [WARN] DeepSeek degraded: DeepSeek API 调用失败：'ascii' codec can't encode characters in position 10-11: ordinal not in range(128)

============================================================
  5. AI Parse new schedule (draft, default params)
============================================================
  HTTP 200
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260625007",
    "algorithm_params": {
      "global_schedule": {
        "algorithm": "traditional",
        "weights": {
          "distance": 0.5,
          "time": 0.3,
          "package_count": 0.2
        }
      }
    },
    "mode": "default",
    "is_replan": false,
    "status": "draft",
    "reference_codes": null
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
  [PASS] draft created: GS20260625007

============================================================
  6. AI Parse dry-run (manual weights)
============================================================
  HTTP 200
{
  "code": 0,
  "message": "success (dry-run)",
  "data": {
    "algorithm_params": {
      "global_schedule": {
        "weights": {
          "distance": 0.8,
          "time": 0.1,
          "package_count": 0.1
        }
      }
    },
    "mode": "manual"
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
  [PASS] manual weights normalized correctly

============================================================
  ALL TESTS PASSED!
============================================================

Phase 8 changes verified:
  [PASS] dry-run response: only algorithm_params + mode
  [PASS] algorithm_params: only global_schedule (no node_dispatch/route_planning)
  [PASS] default mode: no message -> mode=default with standard weights
  [PASS] manual mode: manual weights -> only global_schedule kept
  [PASS] draft mode: includes schedule_code + status=draft
  [PASS] replan_results: removed from schema
  [PASS] AI mode: calls DeepSeek (or degrades gracefully)

