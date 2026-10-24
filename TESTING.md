# HungsOS TESTING checklist

Use this list to test the current GitHub `main` build on the ESP32-S3 N16R8. Check items only after actually testing them.

## DOPE AI — Neural Reaction Lab

- [ ] HungsOS starts normally after syncing the latest `app.py` from GitHub.
- [ ] The home screen shows the **DOPE AI** app icon.
- [ ] Opening `/dope` loads the Neural Reaction Lab without a server error.
- [ ] The first screen shows a cold-start guess and zero rounds.
- [ ] **Run reaction** displays an emoji outcome and updates the round count.
- [ ] Correct guesses, accuracy, and recent lab log update after each round.
- [ ] The transition-count model changes its guess/confidence as it observes more outcomes.
- [ ] Refreshing the page keeps the lab stats in that browser (localStorage).
- [ ] **Reset experiment** clears the stats and transition history.
- [ ] The layout is usable on a narrow phone screen.
- [ ] Existing HungsOS apps still open normally.

## Safety and scope

- [ ] Confirm the lab has no betting, real money, purchases, or prizes.
- [ ] Confirm the interface explains that this is a simple adaptive rule, not a trained neural network.
- [ ] Confirm the random outcomes are not presented as predictable or as a way to win money.

## Test notes

- **Board:** ESP32-S3 N16R8
- **Firmware:** MicroPython
- **Tested on hardware:** Not yet confirmed
- **GitHub source of truth:** `main` branch
- **Latest DOPE AI commit:** `062d6ecb0bcf9cb22eb07e31a9b4472a1e3a09b3`
