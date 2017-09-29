/**
 This Source Code is licensed under the MIT license. If a copy of the
 MIT-license was not distributed with this file, You can obtain one at:
 http://opensource.org/licenses/mit-license.html.
 @author: Manuel Overdijk (manueloverdijk)
 @license MIT
 @copyright Manuel Overdijk, 2015
 */
"use strict"

var MyoProtocol = require('./myoProtocol');
var noble = require('noble');
var Armband = require('./armband/armband');
var EventEmitter = require("events").EventEmitter;

class Agent extends EventEmitter{

    get armbands(){return this._armbands}
    set armbands(value){this._armbands = value}

    constructor(){
        super();
        this.myoProtocol = new MyoProtocol();
        this.MAACaddress = "111111111";
        this._armbands = [];
        this.startDiscover();
        this.port = 1;
        this.ipAdd = "localhost";
        this.debug = 0;
    }

    /**
     * startDiscover
     * Start discovering MYO peripherals
     */

    startDiscover(){
        noble.on('stateChange', function(state){
            this.emit('stateChange', state);

            /* Start discovering Myo peripherals */
            if (state === 'poweredOn') {
                this.discover(this.MAACaddress);
            } else {

                /* Set all armbands to not connected */
                for(let armband of this.armbands){
                    console.log("Disconnecting Armbands");
                    armband.setConnected(false);
                }
                throw new Error('Bluetooth Adapter not found');

            }
        }.bind(this));
    }

    /**
     * Discovers peripherals which advertise given UUID
     * @param UUID
     */
    discover(addr){
        console.log('Starting to scan for MYO devices');
        if(this.debug >= 1){
            console.log("In discovery: " + addr);
            console.log("Noble connection state: " + noble.state);
        }
        noble.startScanning("d5060001a904deb947482c7f4a124842",false);
        noble.on('discover', function (peripheral) {
            console.log("Discovered an armband with ID: " + peripheral.id);
            return;

            var idMatch = addr.indexOf(peripheral.id);  // -1 if no match

            console.log("Element match: " + idMatch );
            if(idMatch != -1){
                let armband = new Armband(peripheral);
                //Set port and IP for armband, indexed based on arrays
                armband.setPort(this.port[idMatch]);
                armband.setIP(this.ipAdd[idMatch]);
                armband.setDebug(this.debug);
                //Log this specific armband
                if(this.debug >= 1){
                    console.log("Peripheral ID: " + peripheral.id + " PORT: " + armband.port + " IP ADDRESS: " + armband.ipAdd);
                }
                this._armbands.push(armband);
                this.emit('discovered', armband);
            }
        }.bind(this));
    }

    /**
     * stopScanning
     */
    stopScanning(){
        noble.stopScanning();
    }

    //Set MAAC address for the agent.
    setAddress(addr){
        this.MAACaddress = addr;
    }

    //Set port. num is an array of ports used
    setPort(num){
        this.port = num;
    }

    //Set IP. Array of all ip addresses used.
    setIP(add){
        this.ipAdd = add;
    }

    //Set debug level
    setDebug(debug){
        this.debug = debug;
    }
}

module.exports = Agent;
