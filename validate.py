"""Run the acceptance battery across every model in the repo.

Exit code is the number of failed checks, so this drops straight into CI.
STEP files are written only for parts that pass cleanly -- a model that
fails its own drawing should not produce a deliverable.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from build123d import export_step

import cadkit

MODELS = ["bracket", "pulley", "transition", "leadscrew", "gearbox"]
OUT = Path("out")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    total_failed = 0
    summary: list[tuple[str, str, int, int, float, float]] = []

    for name in MODELS:
        module = importlib.import_module(f"models.{name}")
        report, part = cadkit.acceptance(module)
        total_failed += report.n_failed

        print(f"\n{module.PART_ID} -- {module.TITLE}")
        print(report.render())

        if report.passed:
            target = OUT / f"{name}.step"
            export_step(part, str(target))
            print(f"  -> {target}")
        else:
            print(f"  !! {report.n_failed} failed, STEP not written")

        summary.append(
            (
                module.PART_ID,
                module.TITLE,
                len(report.rows) - report.n_failed,
                len(report.rows),
                part.volume,
                part.volume * module.DENSITY,
            )
        )

    print("\n" + "=" * 74)
    print(f"{'PART':<9}{'NAME':<34}{'CHECKS':>9}{'VOLUME mm3':>13}{'MASS g':>9}")
    for pid, title, ok, n, vol, mass in summary:
        print(f"{pid:<9}{title[:33]:<34}{f'{ok}/{n}':>9}{vol:>13,.0f}{mass:>9.0f}")
    print("=" * 74)
    print("ALL PASS" if total_failed == 0 else f"{total_failed} CHECK(S) FAILED")
    return total_failed


if __name__ == "__main__":
    sys.exit(main())
