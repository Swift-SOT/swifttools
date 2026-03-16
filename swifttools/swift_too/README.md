# The `swift_too` Python Module

## Swift TOO API client (`swifttools` 4.0 / `swift_too` 2.0)

`swift_too` is a Python package that helps you talk to the Swift TOO API.
In plain terms, it lets you ask the Swift TOO API for information and submit
observation requests from Python code instead of filling everything in manually
on a web page.

You can use it for things like:

- Creating and submitting TOO requests
- Querying observations and plans
- Target visibility calculations
- GUANO metadata access
- Data download helpers
- Name resolution and clock/SAA utilities

This version is built with strongly typed Pydantic models. That means your
inputs are checked more carefully, and error messages are usually clearer when
something is missing or in the wrong format. It also supports both normal
step-by-step requests and asynchronous requests for faster parallel queries.

## What changed in 2.0

- The internals were updated to use the newer REST API design, with typed
  request and response models.
- You can now make async calls directly with the methods `await obj.get()` and
  `await obj.post()`.
- You can also start a request in the background with `obj.queue()` and then
  check `obj.complete` to see when it has finished.
- Validation is stricter, and status/error reporting is more consistent.
- The older `QueryJob` class is no longer supported in this version.

## Import style

Preferred class names are the short forms:

```python
from swifttools.swift_too import TOO, ObsQuery, PlanQuery, VisQuery, Resolve
```

Older names with the `Swift_` prefix are still available for compatibility, but
for new code the short names are easier to read and are the recommended style.

## Authentication

- Read-only queries usually work anonymously by default.
- Submitting a TOO request requires your registered `username` and
  `shared_secret`.

## Quick examples

### 1. Submit a TOO request (synchronous)

```python
from swifttools.swift_too import TOO

too = TOO(
  target_name="SMC X-3",
  target_type="Be/XRB",
  ra=13.023439,
  dec=-72.434508,
  instrument="XRT",
  obs_type="Light Curve",
  xrt_countrate=0.1,
  exp_time_per_visit=3000,
  num_of_visits=14,
  monitoring_freq="2 days",
  immediate_objective="Monitor current outburst evolution.",
  science_just=(
    "We request monitoring to measure flux and timing evolution during "
    "the early outburst phase."
  ),
  exp_time_just="3 ks per visit is required for the planned timing analysis.",
  urgency=2,
  username="your_username",
  shared_secret="your_shared_secret",
)

ok = too.submit()
print(ok, too.status.status, too.status.too_id, too.status.errors)
```

### 2. Run a visibility query (synchronous)

```python
from swifttools.swift_too import VisQuery

vis = VisQuery(name="Crab")
ok = vis.submit()

if ok:
  print(vis.status.status)
  for win in vis.windows[:3]:
    print(win.begin, win.end, win.length)
else:
  print(vis.status.errors)
```

### 3. Run API requests asynchronously with `asyncio`

```python
import asyncio
from swifttools.swift_too import VisQuery


async def main():
  targets = ["Crab", "Vela Pulsar", "Cyg X-1"]
  queries = [VisQuery(name=t) for t in targets]

  # Execute requests concurrently
  results = await asyncio.gather(*(q.get() for q in queries), return_exceptions=True)

  for t, q, r in zip(targets, queries, results):
    print(t, r, q.status.status)


asyncio.run(main())
```

### 4. Use background queue mode

```python
import time
from swifttools.swift_too import VisQuery

q = VisQuery(name="M31")
queued = q.queue()

if queued:
  while not q.complete:
    time.sleep(0.2)
  print(q.status.status, q.status.errors)
```

## Notes for older code

- `QueryJob` is no longer supported in this version.
- For asynchronous code, call methods on the same API object you created
  (`queue()`, `get()`, `post()`), then check that object's `status`, `errors`,
  and `warnings`.

## Additional examples

If you want complete, real examples, open the notebooks in the `examples/`
folder. They walk through TOO submission, visibility checks, plan/observation
queries, and asynchronous examples step by step.
