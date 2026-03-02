# Troubleshooting

## `libaeron` fails to load

Symptoms:
- `LibraryLoadError`
- `Aeron error unavailable: libaeron is not loaded`

Checks:
1. Verify the library exists.
2. Set `AERON_LIBRARY_PATH` explicitly.
3. Confirm loader visibility (`ldconfig -p | grep aeron` on Linux, `PATH` on Windows).

Linux example:

```bash
export AERON_LIBRARY_PATH=/opt/aeron/lib/libaeron.so
```

Windows PowerShell example:

```powershell
$env:AERON_LIBRARY_PATH = "C:\\aeron\\lib\\aeron.dll"
```

## Required symbols missing

Symptom:
- `UnsupportedAeronVersionError`

Cause:
- Installed `libaeron` does not export symbols required by this `pyaeron` version.

Actions:
1. Upgrade/downgrade `libaeron` to a compatible version.
2. Regenerate declarations from the target header:

```bash
make generate-cdef
```

## Timeouts when adding publication/subscription

Symptom:
- `TimedOutError` from `Client.add_publication`/`add_subscription`

Checks:
1. Media driver is running.
2. `Context.aeron_dir` points to the same directory as the media driver.
3. Channel URI is valid.
4. Increase timeout temporarily to diagnose slow startup.

## Publication offer failures

Common exceptions:
- `NotConnectedError`
- `BackPressuredError`
- `AdminActionError`

Actions:
1. Use `offer_with_retry` for transient states.
2. Ensure subscriber is connected (`Publication.is_connected`).
3. Verify stream/channel match between publisher and subscriber.

## No messages received

Checks:
1. Same channel and stream ID on both ends.
2. Poll loop running (`Subscription.poll` or `poll_until`).
3. Handler not raising exceptions.
4. For UDP, verify endpoint/port binding and local firewall.

## Invoker mode stalls

If using `Context(use_conductor_agent_invoker=True)`, the application must call:
- `Client.do_work()` periodically.

Without conductor work, add/remove operations and resource setup may not progress.

## CnC initialization errors

Symptom:
- `TimedOutError`/`AeronError` constructing `CnC(...)`

Checks:
1. `aeron_dir` is correct.
2. `cnc.dat` exists in that directory.
3. Driver is up and has initialized CnC file.
4. Increase `timeout_ms` for slow environments.
