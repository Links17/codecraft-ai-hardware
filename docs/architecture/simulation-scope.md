# Simulation scope decision

Decision date: 2026-11-18, Asia/Shanghai. This resolves the scope decision in
[OPT-17](../development/optimization-plan.md), without introducing another
optimization item or changing a Target's physical support status.

## Decision

Retain `simulate.supported: false` in the ESP-IDF, Linux and Arduino platform
manifests. No simulator execution is registered or claimed. This is a decision
about this repository's maintained workflows, not a claim that its processors
cannot be emulated. No emulator was installed or run for this assessment.

The concrete scenario evaluated is E1001/E1002 SHT4x command → conversion →
receive, including CRC errors, timeouts, retry and access by another I2C device
during conversion. This scenario already has a deterministic execution path in
[the shared component tests](../../tests/platforms/esp-idf/components/codecraft_sht4x/failure_cases.c)
and [the host runner](../../tests/platforms/esp-idf/components/codecraft_sht4x/test_sensor_drivers.py). These
tests execute the actual C protocol and board bindings using narrow SDK doubles;
they are host tests, not a whole-board simulator.

## Candidates and evidence

| Candidate | Relevant evidence | Assessment for the selected scenario |
| --- | --- | --- |
| Espressif QEMU | The ESP-IDF **v6.0.2** guide supports ESP32-S3 CPU/memory emulation and describes a virtual framebuffer that is not a physical peripheral. The linked QEMU feature matrix lists I2C, I2S and general-purpose SPI as unimplemented. | It cannot cover the selected native I2C transaction with that documented model. Substituting the framebuffer would not validate this board's panel, buses or power sequencing. |
| Espressif esp-emulator virtual parts | Its parts guide documents virtual I2C/SPI devices and an SHT31 example, with board wiring supplied separately. | This provides a possible future integration path, but the reviewed example is not an SHT4x/PCF8563 model. This repository has no pinned, reviewed part models, board fixture or passing native-driver simulator case for these Targets. |

Sources checked on the decision date: [ESP-IDF v6.0.2 QEMU guide](https://docs.espressif.com/projects/esp-idf/en/v6.0.2/esp32s3/api-guides/tools/qemu.html),
[Espressif QEMU feature matrix](https://github.com/espressif/esp-toolchain-docs/blob/main/qemu/README.md),
and [Espressif virtual-parts guide](https://github.com/espressif/esp-emulator/blob/main/docs/guides/PARTS.md).
The candidate assessments are repository engineering judgments from those
sources, not vendor guarantees. Upstream main-branch documentation may change;
recheck it and pin an actual tool/model version before adopting a simulator.

## Coverage and reopening criteria

Host failures test state, cleanup, decoding and serialization. They do not
establish electrical timing, sensor accuracy, power/reset behavior, DMA/PSRAM
pressure, interrupt latency or combined peripheral behavior. Native builds and
revision-specific physical evidence remain separate acceptance steps.

Linux keeps its Python/source and device-tree checks; they do not emulate the
reTerminal kernel, overlays or physical devices. Arduino has registered
Grove Beginner Kit and Wio Terminal Targets, but no registered simulator. Neither platform is promoted to simulator support by the
ESP-IDF candidate assessment.

Revisit this decision only for a concrete scenario requiring firmware/driver
integration beyond the existing host tests. Register its pinned simulator,
attributable models, board wiring, expected observations and explicit fidelity
limits together with a reproducible gate case under the owning Platform/Target.
A passing simulation may record simulation evidence, never physical evidence.

## V0.2 status

This remains the current implementation limit. It does not satisfy the later V0.2 requirement for a first simulator executing a concrete user-project scenario. [V02-07](../development/v0.2-todo.md) tracks that implementation and its acceptance; host fixtures remain host tests.
