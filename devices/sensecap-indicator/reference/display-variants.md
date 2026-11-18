# SenseCAP Indicator display variants

This source record supports OPT-06. It describes panel assembly choices, not
an observed PCB revision or successful physical validation.

## Pinned vendor evidence

Repository: Seeed-Solution/SenseCAP_Indicator_ESP32, commit
`77edb8d2b9a92fc67965c1b2d4a838f0d09a1800`, inspected 2026-11-18.
The repository's Apache-2.0 license applies to its source implementation.

| File | Source and SHA-256 |
| --- | --- |
| Kconfig.projbuild | [Pinned source](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32/blob/77edb8d2b9a92fc67965c1b2d4a838f0d09a1800/components/bsp/Kconfig.projbuild); `c98d6e5506d471630e3a8b8a154956c20a57b8ebcf793932c75bdf930ac214fe` |
| sensecap_indicator_board.c | [Pinned source](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32/blob/77edb8d2b9a92fc67965c1b2d4a838f0d09a1800/components/bsp/src/boards/sensecap_indicator_board.c); `fe1b67a80a9d84baceb41dd62e8590986003922111f5e501feab061585a93d77` |
| lcd_panel_config.c | [Pinned source](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32/blob/77edb8d2b9a92fc67965c1b2d4a838f0d09a1800/components/bsp/src/boards/lcd_panel_config.c); `e0db50a81b3e70c1adc10efffb0d4a4a6ad0ce0860304d77b4ffaf6e94d8a808` |
| LICENSE | [Pinned source](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32/blob/77edb8d2b9a92fc67965c1b2d4a838f0d09a1800/LICENSE); `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd` |

## Assembly facts and native behavior

Common display interface: RGB. Both vendor choices use 480 by 480 pixels,
a 16-bit RGB data bus and the same declared 18 MHz clock and porch/pulse timing.
The existing pin/timing definitions remain unchanged.

GX panel supplier: GuanXian. GX register controller: ST7701S.
GX initialization: SPI+RGB. The vendor calls lcd_panel_st7701s_init after RGB
initialization. The existing native register sequence remains the GX path.

DX panel supplier: DaXian. DX initialization: RGB-only.
After RGB initialization, the vendor sets expander LCD CS and LCD RESET high,
then configures both as outputs. It does not send the GX register sequence.
The DX controller identity is not established by the cited source; the vendor's
null controller label is a software marker, not a physical controller name.

These choices are not mappings from product names or serial numbers to PCB
revisions. Neither a verified revision list nor a board-specific panel
identification procedure is available in this record. Do not infer the panel
from the D1/D1S/D1L/D1Pro product label or a successful compiler result.

## Acceptance boundary

Software selection must identify GX or DX explicitly in the project and lock,
reject unknown choices, and retain the actual native compile definition in its
build evidence. The historical default can only describe the original GX
build profile; it is not automatic physical detection.

Physical acceptance requires an identified board/revision, attributable panel
identity, authorized deployment and observed display/touch/recovery results.
Those observations remain not_run. Image licensing/revision matching and
runtime resource measurements remain separate acceptance items.
