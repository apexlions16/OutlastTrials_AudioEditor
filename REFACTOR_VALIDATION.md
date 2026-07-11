# Refactor Validation

This refactor was performed as a behavior-preserving split of the upstream
`v1.1.2` monolith. It intentionally avoids redesigning business logic while the
package boundary is being established.

## Automated checks

- All package modules import successfully in a headless Qt environment.
- The historical launcher remains below 30 lines.
- All upstream AST-defined classes and top-level functions remain present.
- Every effective upstream class member remains available at runtime, including
  methods distributed across `WemSubtitleApp` mixins.
- All Python sources parse and byte-compile successfully.
- Wwise project creation has targeted tests for paths containing spaces, existing
  projects, and protection of non-empty project directories.
- The main window was constructed and closed successfully with the bundled
  runtime assets available.

## Mechanical equivalence audit

The effective upstream API contains 461 class methods after applying Python's
normal “last definition wins” behavior to repeated definitions. AST comparison
against the modular source found:

- 461/461 effective methods present.
- 460/461 method bodies mechanically equivalent after normalizing application
  root lookup from the monolith's `__file__` to `APP_ROOT`.
- One intentional behavior change:
  `WavToWemConverter.ensure_project_exists`.

The intentional change prevents deletion of a non-empty project directory and
passes the `.wproj` path to `subprocess.run(..., shell=False)` without embedding
literal quote characters.

## Removed dead definitions

The earlier, unreachable versions of these repeated definitions were removed;
the final effective implementations were retained:

- `WavToWemConverter.convert_single_file`
- `WemSubtitleApp._on_scan_finished`
- `WemSubtitleApp.batch_adjust_volume`
- `WemSubtitleApp.update_conversion_status`

## Remaining validation boundary

The checks above do not replace an end-to-end test on Windows with Wwise
2019.1.6.7110, a real The Outlast Trials installation, representative BNK/WEM
files, and deployment to the game directory. That environment should be used
before publishing a release build.
