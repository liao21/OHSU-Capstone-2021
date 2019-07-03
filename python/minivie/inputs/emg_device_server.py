#!/usr/bin/env python3
""" EMG Device Server Simulator

This function serves as a SIMULATOR for an EMG device websocket streaming device with 16ch @ 2kHz.
For the purposes of simulation, this server generates random data on all channels

For help with websockets see:
https://websockets.readthedocs.io/en/stable/intro.html

Raw EMG API specs

The sample field contains 16 shorts, corresponding to 16 electrode channels. Each short is a 12-bit,
 digitized value between 0-4095 with a midpoint of 2047. These values map to 0V - 2.5V analog voltages.

Data is published to a websockets port in batches at a rate of 125 batches/sec
(so each batch contains 16 time samples).

Things to consider:
- Installation of service
- Consume data via Websocket (https://websockets.readthedocs.io/en/stable/intro.html)
- Accommodate sampling rate of 2kHz (batch rate of 125Hz)


Note: results can be viewed in a web browser using the following HTML / javascript / jquery example:
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>WebSocket demo</title>
            <script src="https://code.jquery.com/jquery-1.12.4.min.js"
            integrity="sha256-ZosEbRLbNQzLpnKIkEdrPv7lOy9C27hHQ+Xp8a4MxAQ="
            crossorigin="anonymous"></script>
            <script>
                var ws = new WebSocket("ws://127.0.0.1:5678/");

                ws.onmessage = function (event) {
                    console.log('msg')
                    $("#msg_status").text(event.data);
                };
            </script>
        </head>
        <body>
            <p>Time: <span id="msg_status"></span></p>
        </body>
    </html>

31JAN2019 Armiger Created
Revisions:

"""


import asyncio
import websockets
import numpy as np
import time
import json


async def send_data(websocket, _path):
    num_channels = 16
    num_samples = 16

    # use these to set emg midpoint and amplitude
    center = 2047
    amp = 250

    # create sample packet
    data = {
        "api_version": "0.8.2",
        "stream_batch": {
            "raw_emg": {
                "samples": [{
                    "data": np.zeros(num_channels, dtype=np.int16).tolist(),
                    "timestamp_s": 0.0
                }] * num_samples,
                "batch_num": 0
            }
        }
    }
    while True:
        data['stream_batch']['raw_emg']['batch_num'] += 1
        # Generate new random samples
        for i in range(0, len(data['stream_batch']['raw_emg_batch']['samples'])):
            new_sample = {"raw_emg": np.random.randint(center-amp, center+amp, size=num_channels, dtype=np.int16).tolist(),
                          "timestamp_s": time.time()}
            data['stream_batch']['raw_emg']['samples'][i] = new_sample
            await asyncio.sleep(0.0005)

        await websocket.send(json.dumps(data))

start_server = websockets.serve(send_data, '127.0.0.1', 9999)
asyncio.get_event_loop().run_until_complete(start_server)
print('Ready to connect')
asyncio.get_event_loop().run_forever()
