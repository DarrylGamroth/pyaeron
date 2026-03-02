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

## `libaeron_driver` fails to load

Symptoms:
- `LibraryLoadError` when creating `MediaDriverContext` or `MediaDriver`

Checks:
1. Verify `libaeron_driver` is installed.
2. Set `AERON_DRIVER_LIBRARY_PATH` explicitly.
3. On Windows, ensure the DLL directory is on `PATH`.

Linux example:

```bash
export AERON_DRIVER_LIBRARY_PATH=/opt/aeron/lib/libaeron_driver.so
```

Windows PowerShell example:

```powershell
$env:AERON_DRIVER_LIBRARY_PATH = "C:\\aeron\\lib\\aeron_driver.dll"
```

## Required symbols missing

Symptom:
- `UnsupportedAeronVersionError`

Cause:
- Installed Aeron library does not export symbols required by this `pyaeron` version.

Actions:
1. Upgrade/downgrade Aeron libraries to a compatible version.
2. Regenerate declarations from the target header:

```bash
make generate-cdef
```

## Timeouts when adding publication/subscription

Symptom:
- `TimedOutError` from `Client.add_publication` or `Client.add_subscription`

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
2. Poll loop is running (`Subscription.poll` or `poll_until`).
3. Handler is not raising exceptions.
4. For UDP, verify endpoint/port binding and local firewall.

## Invoker mode stalls

If using `Context(use_conductor_agent_invoker=True)`, the application must call:
- `Client.do_work()` periodically.

Without conductor work, add/remove operations and resource setup may not progress.

## CnC initialization errors

Symptom:
- `TimedOutError` or `AeronError` constructing `CnC(...)`

Checks:
1. `aeron_dir` is correct.
2. `cnc.dat` exists in that directory.
3. Driver is up and has initialized CnC file.
4. Increase `timeout_ms` for slow environments.

## Integration tests cannot find driver state

Symptom:
- Integration tests skipped or fail due to missing driver/CnC

Checks:
1. If using an external driver, set `AERON_EXTERNAL_MEDIA_DRIVER_DIR` to the directory containing `cnc.dat`.
2. If using managed-driver mode, ensure `aeronmd` is installed or set `AERON_MD_BINARY`.
