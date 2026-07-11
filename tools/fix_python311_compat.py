"""Normalize source constructs that are valid only with Python 3.12+ parsing."""

from __future__ import annotations

from pathlib import Path


TARGET = Path("outlast_trials_audio_editor/ui/mixins/language_tabs.py")
KEYS = ("duration", "size", "sample_rate", "bitrate", "channels")


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    original = source

    for key in KEYS:
        invalid = (
            f'modified_info_layout.addRow(f"{{self.tr("{key}")}}", '
            f'modified_info_labels["{key}"])'
        )
        valid = (
            f'modified_info_layout.addRow(self.tr("{key}"), '
            f'modified_info_labels["{key}"])'
        )
        source = source.replace(invalid, valid)

    if source != original:
        TARGET.write_text(source, encoding="utf-8")
        print(f"Python 3.11 uyumluluğu düzeltildi: {TARGET}")
    else:
        print("Python 3.11 uyumluluk düzeltmesi gerekmiyor.")

    remaining = [key for key in KEYS if f'f"{{self.tr("{key}")}}"' in source]
    if remaining:
        raise RuntimeError(f"Düzeltilemeyen Python 3.12+ f-string ifadeleri: {remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
