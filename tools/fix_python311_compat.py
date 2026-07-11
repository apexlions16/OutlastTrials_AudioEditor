"""Normalize source constructs that are valid only with Python 3.12+ parsing."""

from pathlib import Path


TARGET = Path("outlast_trials_audio_editor/ui/mixins/language_tabs.py")
REPLACEMENTS = {
    'modified_info_layout.addRow(f"{self.tr("duration")}", modified_info_labels["duration"])':
        'modified_info_layout.addRow(self.tr("duration"), modified_info_labels["duration"])',
    'modified_info_layout.addRow(f"{self.tr("size")}", modified_info_labels["size"])':
        'modified_info_layout.addRow(self.tr("size"), modified_info_labels["size"])',
    'modified_info_layout.addRow(f"{self.tr("sample_rate")}", modified_info_labels["sample_rate"])':
        'modified_info_layout.addRow(self.tr("sample_rate"), modified_info_labels["sample_rate"])',
    'modified_info_layout.addRow(f"{self.tr("bitrate")}", modified_info_labels["bitrate"])':
        'modified_info_layout.addRow(self.tr("bitrate"), modified_info_labels["bitrate"])',
    'modified_info_layout.addRow(f"{self.tr("channels")}", modified_info_labels["channels"])':
        'modified_info_layout.addRow(self.tr("channels"), modified_info_labels["channels"])',
}


def main():
    source = TARGET.read_text(encoding="utf-8")
    original = source

    for invalid, valid in REPLACEMENTS.items():
        source = source.replace(invalid, valid)

    if source != original:
        TARGET.write_text(source, encoding="utf-8")
        print("Python 3.11 uyumluluğu düzeltildi: " + str(TARGET))
    else:
        print("Python 3.11 uyumluluk düzeltmesi gerekmiyor.")

    remaining = [invalid for invalid in REPLACEMENTS if invalid in source]
    if remaining:
        raise RuntimeError("Düzeltilemeyen Python 3.12+ f-string ifadeleri bulundu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
