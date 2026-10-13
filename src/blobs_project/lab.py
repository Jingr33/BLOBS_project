"""Lab bench tool for the left tower: tare the sensor, drive the pump, log the level.

    uv run python -m blobs_project.lab tare
    uv run python -m blobs_project.lab run 0 --zero-v 0.245      # watch, pump off
    uv run python -m blobs_project.lab run 4                     # hold 4 V
    uv run python -m blobs_project.lab run 3 4 5 --hold 180 --csv data/step.csv

Add --mock to rehearse without the card. The pump ramps at 1 V/s, is capped at
--max-v (default 5 V, at most 7.5 V) and goes to 0 V on exit, Ctrl+C or error.
"""

import argparse
import itertools
import os
import sys
import time
from collections.abc import Sequence
from typing import TextIO

from blobs_project import config
from blobs_project.backend import NIDAQ, HardwareError, MockDAQ, Tower
from blobs_project.backend.hardware import TowerCalibration


def ramp(tower: Tower, target: float) -> None:
    """Move the pump to ``target`` volts in 0.1 V steps at 1 V/s."""
    while abs(target - tower.pump_voltage) > 0.1:
        step = 0.1 if target > tower.pump_voltage else -0.1
        tower.set_pump_voltage(tower.pump_voltage + step)
        time.sleep(0.1)
    tower.set_pump_voltage(target)


def run(
    tower: Tower, volts: Sequence[float], hold: float | None, period: float, log: TextIO
) -> None:
    """Hold the pump at each of ``volts`` for ``hold`` s (None: until Ctrl+C).

    Prints and writes a CSV row to ``log`` every ``period`` s.
    """
    start = time.monotonic()
    for target in volts:
        ramp(tower, target)
        samples = itertools.count() if hold is None else range(round(hold / period))
        for _ in samples:
            t, pump = time.monotonic() - start, tower.pump_voltage
            raw, level = tower.read_level_v(), tower.read_level_cm()
            print(f"{t:7.1f} s  pump {pump:4.2f} V  ai0 {raw:6.3f} V  {level:6.2f} cm")
            log.write(f"{t:.3f},{pump:.3f},{raw:.4f},{level:.3f}\n")
            time.sleep(period)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Return the parsed ``argv``; bad voltages exit with code 2."""
    fmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser("lab", description=__doc__, formatter_class=fmt)
    parser.add_argument("--mock", action="store_true", help="use MockDAQ, no card")
    parser.add_argument("--zero-v", type=float, default=config.TOWER_LEVEL_ZERO_V)
    sub = parser.add_subparsers(dest="command", required=True)
    tare = sub.add_parser("tare", help="measure the sensor zero (empty tank)")
    tare.add_argument("--samples", type=int, default=30, help="readings, 0.5 s apart")
    p = sub.add_parser("run", help="hold the pump at each voltage, logging the level")
    p.add_argument("volts", type=float, nargs="+")
    p.add_argument("--hold", type=float, help="seconds per voltage (default: forever)")
    p.add_argument("--max-v", type=float, default=5.0, help="pump cap, at most 7.5 V")
    p.add_argument("--period", type=float, default=0.5, help="sample period [s]")
    p.add_argument("--csv", help="also write samples to this CSV file")
    args = parser.parse_args(argv)
    if args.command == "run":
        cap = min(args.max_v, config.TOWER_PUMP_MAX_V)
        if not all(0 <= v <= cap for v in args.volts):
            parser.error(f"pump voltages must be within 0..{cap} V")
        if len(args.volts) > 1 and args.hold is None:
            parser.error("--hold is needed with more than one voltage")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI; return 0 if OK, 1 on a hardware error."""
    args = parse_args(argv)
    cap = config.TOWER_PUMP_MAX_V
    max_v = min(getattr(args, "max_v", cap), cap)
    cal = TowerCalibration(zero_v=args.zero_v, max_pump_v=max_v)
    tower = Tower(MockDAQ() if args.mock else NIDAQ(), cal)
    try:
        with tower:
            if args.command == "tare":
                zero = tower.tare(args.samples)
                print(f"zero {zero:.4f} V  ->  pass --zero-v {zero:.4f}")
                return 0
            with open(args.csv or os.devnull, "w") as log:
                log.write("t_s,ao_v,ai0,level_cm\n")
                run(tower, args.volts, args.hold, args.period, log)
    except KeyboardInterrupt:
        print("\nStopped, pump at 0 V.")
    except HardwareError as e:
        print(f"Hardware error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
