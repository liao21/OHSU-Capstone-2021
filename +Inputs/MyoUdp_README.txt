-------------
Windows Installation Notes:
-------------
The helper program MyoUdp.exe based is on the
Myo Armband SDK for streaming EMG data.  This executable requires the
Microsoft Visual Studio 2013 Redistributable Package.  If it is not
installed, you may get an error about missing DLL files.
http://www.microsoft.com/en-us/download/confirmation.aspx?id=40784

-------------
Mac Installation Notes:
-------------
Unzip the MyoUdp-Mac.zip file to a local directory.  Open terminal and launch the program.  Ensure execute permissions are set for MyoUdp


-------------
Usage: 
-------------
> MyoUdp <IP_Destination> <Port Destination> <0|1 Enable wake vibration>


-------------
Examples:
-------------

[Launch MyoUDP with default arguments (IP=127.0.0.1 Port=10001 Vibration=0)]
> MyoUdp 

[Launch MyoUDP with custom address and port]
> MyoUdp 192.168.1.100 10001


-------------
Revisions:
-------------

1/18/2016 Armiger: Created
1/10/2019 Armiger: Added a mac version of hte program and added enable/disable of wakeup vibration
