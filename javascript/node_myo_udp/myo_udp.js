var MyoBluetooth  = require('MyoNodeBluetoothAPL');
var MyoAgent = new MyoBluetooth();
var maacAddress = process.argv[2].toLowerCase();
MyoAgent.setAddress(maacAddress);
console.log(MyoAgent.MAACaddress);

MyoAgent.on('discovered', function(armband){
	armband.on('connect', function(connected){
    
    	// armband connected succesfully
        if(connected){
            // discover all services/characteristics and enable emg/imu/classifier chars
        	this.initStart();
    	} else {
    	  // armband disconnected
   		}

	});
    
    // Armband receives the ready event when all services/characteristics are discovered and emg/imu/classifier mode is enabled
    armband.on('ready', function(){
   

    	// register for events
        armband.on('batteryInfo',function(data){
        	console.log('BatteryInfo: ', data.batteryLevel);

		
		});
        
        // read or write data from/to the Myo
        armband.readBatteryInfo();
		armband.setMode();
		armband.on('emg', function(data1){
			console.log("EMG DATA: " + data1.emgData.sample2);
			process.stdout.clearLine();
			process.stdout.cursorTo(0);
			//console.log('EMG Data: ',data2.sample1);
			//console.log('EMG Data: ',data2.sample2);
		});	
    });
	
   
    
   armband.connect();
});