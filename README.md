# Crossing Chickens

On-board software for the Arduino UNO Q crossing node. The camera, tracker, and crossing lights keep running locally. `publisher/` sends telemetry to the city dashboard in [egg-dashboard](https://github.com/AlpMeteSenel/egg-dashboard).

- `vision/` is the node application: capture, detection, the local dashboard, and crossing or bus-stop behavior.
- `publisher/` reads that local state and uploads it. It does not open the camera.
- `firmware/` is the MCU sketch for the 30-LED strip.

The node stores its own settings and upload queue on the board. Those files, credentials, and camera frames are not in this repository.
