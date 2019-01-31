#!/usr/bin/env python

# WS server that sends messages at random intervals
#
# https://websockets.readthedocs.io/en/stable/intro.html

# Raw EMG API specs

# The sample field contains 16 shorts, corresponding to the 16 electrode channels on our band. Each short is a 12-bit,
#  digitized value between 0-4095 with a midpoint of 2047. These values map to 0V - 2.5V analog voltages.

# Data is published to a websockets port in batches at a rate of 125 batches/sec
# (so each batch contains 16 time samples).

# Things to consider:
# - Installation of service
# - Consume data via Websocket (https://websockets.readthedocs.io/en/stable/intro.html)
# - Accommodate sampling rate of 2kHz (batch rate of 125Hz)

import asyncio
import datetime
import random
import websockets
import numpy as np


async def send_data(websocket, _path):
    count = 2047
    while True:
        #data = np.zeros((16, 16), dtype=np.int16)         
        #data[:,0] = np.random.randint(100, 200, size=(1, 16), dtype=np.int16)
        #data[:,1] = np.random.randint(300, 400, size=(1, 16), dtype=np.int16)
        #data[:,2] = np.random.randint(500, 600, size=(1, 16), dtype=np.int16)
        #data[:,3] = np.random.randint(700, 800, size=(1, 16), dtype=np.int16)
        data = np.random.randint(2047-250, 2047+250, size=(16, 16), dtype=np.int16)
        #data = count*np.ones((16, 16), dtype=np.int16)
        await websocket.send(data.astype('h').tostring())
        #await asyncio.sleep(0.008)
        await asyncio.sleep(0.008)
        count += 1
        if count > 4095:
            count = 2047
        

start_server = websockets.serve(send_data, '127.0.0.1', 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
