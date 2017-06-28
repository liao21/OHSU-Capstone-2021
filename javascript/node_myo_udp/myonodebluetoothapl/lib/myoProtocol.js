/**
 This Source Code is licensed under the MIT license. If a copy of the
 MIT-license was not distributed with this file, You can obtain one at:
 http://opensource.org/licenses/mit-license.html.
 @author: Manuel Overdijk (manueloverdijk)
 @license MIT
 @copyright Manuel Overdijk, 2015
 */
"use strict"

class MyoProtocol {

    get services(){ return this._services}
    set services(services){this._services = services};

    constructor(){

        this._services = {
            control: {
                id: "d5060001a904deb947482c7f4a124842",
                MYO_INFO: "d5060101a904deb947482c7f4a124842",
                FIRMWARE_VERSION: "d5060201a904deb947482c7f4a124842",
                COMMAND: "d5060401a904deb947482c7f4a124842"
            },
            imuData: {
                id: "d5060002a904deb947482c7f4a124842",
                IMU_DATA : "d5060402a904deb947482c7f4a124842"
            },
            classifier: {
                id: "d5060003a904deb947482c7f4a124842",
                classifierEvent: "d5060103a904deb947482c7f4a124842"
            },
            emgData: {
                id: "d5060005a904deb947482c7f4a124842",
                EMG_DATA_0: "d5060105a904deb947482c7f4a124842",
                EMG_DATA_1: "d5060205a904deb947482c7f4a124842",
                EMG_DATA_2: "d5060305a904deb947482c7f4a124842",
                EMG_DATA_3: "d5060405a904deb947482c7f4a124842"
            },
            battery: {
                id: "180f",
                BATTERY_LEVEL: "2a19"
            },
            genericAccess: {
                id: "1800",
                DEVICE_NAME: "2a00"
            }
        }

    }
}

module.exports = MyoProtocol;

