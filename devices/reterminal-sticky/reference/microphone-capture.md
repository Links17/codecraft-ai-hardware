# Capture microphone audio on demand with ESP-IDF

Source: Seeed's [ESP-IDF Pages and Peripherals](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-pages/). APIs below belong to `Sticky_dashboard_demo`.

## Trigger capture explicitly

The official Microphone page does **not** capture automatically when opened. It displays `Press AI button to sample` until a short press of AI / OK / Power button produces `AppEvent::RefreshPage` while `PageId::Microphone` is active.

```text
AI short press on Microphone page
-> RefreshPage
-> update_microphone()
-> sticky_microphone_capture()
-> AppState.microphone
-> Microphone Page Renderer
```

Check both the current page and event type before capturing. This prevents a refresh action on another page from starting an unintended recording.

## Scope power and state to one sample

The Device module enables microphone power and the PDM receive channel for an approximately **one-second** capture, then disables both immediately afterward. Keep this resource management in the Device module, not in the Renderer.

Record at least:

- `captured`: whether a capture was attempted;
- `valid` and `error`: whether it succeeded and why it failed;
- RMS, Peak, and volume percentage when the read succeeds.

The Renderer only draws those stored values or an error message. It must not enable PDM, read samples, or refresh e-paper directly. Reuse the normal App refresh flow after the capture result has been stored.
