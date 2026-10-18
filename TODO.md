# Application completion checklist

Status reflects the current branch. Code marked complete is implemented and
covered by automated tests; it does not substitute for physical commissioning.
Do not operate a live pump until the remaining hardware safety and acceptance
checks are complete.

## Implemented

- [x] Closed-loop PI control runs on measured tower level; the simulated two-tank
  plant is the default fallback when no NI card is configured.
- [x] NI-DAQ and tower interfaces provide configurable channels, sensor
  calibration, pump output clamping, and cleanup on normal/error exits.
- [x] Regulation setpoints and scenario CSV values are constrained to the
  configured range; pump output is limited to the configured 7.5 V maximum.
- [x] Median filtering, repeated-invalid-reading shutdown, high-level trip,
  hardware read/write fault handling, pump/flow/power display, and a UI
  emergency-stop action are implemented.
- [x] Faults are logged and displayed. If a stop write fails, the pump state is
  marked unknown, the last confirmed output is retained in the UI, and a new
  regulation run is blocked until a zero write succeeds.
- [x] A level-trend observer projects the recent rising level over a 10-second
  horizon and raises an operator warning before the warning threshold is
  reached; the independent measured-level trip remains in place.
- [x] `TowerCalibration` rejects invalid calibration values and pump caps above
  the approved software limit.
- [x] Scenario CSV import/export, recorded-run export/re-import, run statistics,
  and the statistics view are implemented.

## Issue #25 — Klárka's predictive level controller

- [x] Cherry-pick and integrate Klárka's model/observer/MPC draft into the
  regulation controller package.
- [x] Linearize and discretize the identified two-tank model at the requested
  setpoint; use a Kalman filter to estimate the unmeasured upper-tank height
  from pump voltage and lower-tank sensor readings.
- [x] Add a finite-horizon MPC with voltage, tank-level, and pump slew
  constraints; preserve the PI controller as an injectable alternative.
- [x] Make MPC the default regulation controller and configure its output limit
  from the active `Tower` calibration.
- [x] Test model validity, observer state estimation, MPC command/slew limits,
  setpoint changes, reset behavior, simulated setpoint tracking, and controller
  failure shutdown.
- [ ] Compare predictive-control behavior with PI using recorded physical runs;
  confirm estimator noise settings, horizon, weights, and tuning with the
  hardware owner before live deployment.

## Issue #27 — Observer and overflow protection

- [x] Bound setpoints and pump voltage; reject unsafe calibration limits.
- [x] Stop regulation on a measured critical level, repeated invalid samples,
  or DAQ errors; log and show the fault.
- [x] Provide an emergency-stop button in the UI and a default zero-output
  startup/stop command.
- [x] Warn on a high measured level or a projected rising-level threshold.
- [x] Make an unconfirmed pump stop visible and prevent restarting while output
  state is unknown.
- [ ] Validate the observer warning against real sensor noise, realistic
  operating data, and overflow test cases; set the forecast horizon and warning
  threshold with the hardware owner.
- [ ] Decide and verify the hardware-independent safe response when the DAQ
  cannot accept the zero-output command. Software cannot guarantee pump-off
  after a driver, USB, or power failure.
- [ ] Verify device-specific output behavior when tasks close, the process exits,
  or USB communication is lost; add an external interlock if required.
- [ ] Verify fault history is retained/exported in the run log as required by
  operators (currently the application logger and UI status report faults).

## Live-hardware integration and commissioning

- [ ] Connect the GUI application lifecycle to the configured NI `Tower`;
  current GUI startup uses the simulated plant by default.
- [ ] Confirm the device name, channel wiring, terminal configuration, sensor
  calibration, pump polarity, and electrical limits on the actual NI card.
- [ ] Run hardware smoke tests with the pump disconnected: device discovery,
  sensor readings, tare, channel mapping, zero-output command, and failure
  handling.
- [ ] Verify output polarity/scaling with appropriate test equipment before
  connecting the pump driver.
- [ ] Test the external emergency stop/interlock and all disconnect/failure
  cases with the pump disconnected first.
- [ ] Conduct initial live tests under hardware-owner supervision using a
  conservative cap and a documented stop procedure.
- [ ] Record commissioning results, approved limits, calibration, controller
  settings, and operator instructions.

## Completion criteria

- [ ] Predictive-control requirements and acceptance tests for issue #25 pass.
- [ ] Issue #27 safety behavior is validated in simulation and on hardware,
  including the response to an unconfirmed stop.
- [ ] The GUI clearly identifies simulation versus live hardware and does not
  start control unless the hardware and output state are safe.
- [ ] Physical commissioning and operating instructions are signed off before
  routine use.
