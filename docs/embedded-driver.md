# Embedded Media Driver

`pyaeron` supports launching an embedded Aeron Media Driver in-process via `libaeron_driver`.

## Basic Usage

```python
from pyaeron import Client, Context, MediaDriver

with MediaDriver.launch_embedded() as driver:
    with Context(aeron_dir=driver.aeron_dir) as ctx:
        with Client(ctx) as client:
            pub = client.add_publication("aeron:ipc", 1001)
            sub = client.add_subscription("aeron:ipc", 1001)
            # ... publish and poll
            pub.close()
            sub.close()
```

## Configuring Driver Context

```python
from pyaeron import MediaDriver, MediaDriverContext, ThreadingMode

ctx = MediaDriverContext(
    aeron_dir="/tmp/pyaeron-embedded",
    dir_delete_on_start=True,
    dir_delete_on_shutdown=True,
    threading_mode=ThreadingMode.SHARED,
)

driver = MediaDriver(ctx, manual_main_loop=False)
try:
    # ...
    pass
finally:
    driver.close()
```

## Manual Main Loop

If `manual_main_loop=True`, call `driver.do_work()` periodically:

```python
driver = MediaDriver.launch_embedded(manual_main_loop=True)
try:
    while work_to_do:
        work = driver.do_work()
        driver.idle_strategy(work)
finally:
    driver.close()
```

## Library Discovery

Embedded mode loads `libaeron_driver` from:
1. `AERON_DRIVER_LIBRARY_PATH`
2. system loader resolution
3. common names (`libaeron_driver.so`, `libaeron_driver.dylib`, `aeron_driver.dll`)
