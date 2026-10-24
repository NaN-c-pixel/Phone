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


## HungsOS Arcade

- [ ] Home screen shows the **Games** icon and `/games` opens HungsOS Arcade.
- [ ] **AI Snake** starts, moves automatically, eats food, and stops on collision.
- [ ] AI Snake's score, best score, and run count update correctly.
- [ ] Starting a second AI run works without overlapping timers.
- [ ] Manual Snake controls work with the arrow buttons or keyboard.
- [ ] AI Snake's saved best/run/caution stats survive a browser refresh.
- [ ] **2048** starts with two tiles and arrow/button moves merge equal tiles correctly.
- [ ] 2048 score updates on merges and a new game resets the board.
- [ ] **Memory Match** reveals cards, counts moves/pairs, and detects completion.
- [ ] The game buttons and boards fit on a narrow phone screen.
- [ ] Existing DOPE AI and the original Snake app still open.

## Arcade notes

- AI Snake uses a lightweight safety/food-seeking heuristic with a small caution adjustment between runs; it is not a neural network.
- 2048 and Memory Match run in the browser and do not need extra MicroPython packages.
- **Tested on physical ESP32:** not yet confirmed.
