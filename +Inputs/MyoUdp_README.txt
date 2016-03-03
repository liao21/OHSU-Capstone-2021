Installation Notes:

The helper program MyoUdp.exe based is on the
Myo Armband SDK for streaming EMG data.  This executable requires the
Microsoft Visual Studio 2013 Redistributable Package.  If it is not
installed, you may get an error about missing DLL files.
http://www.microsoft.com/en-us/download/confirmation.aspx?id=40784


Usage: 

> MyoUdp.exe <IP_Destination> <Port Destination>


Examples:

[Launch MyoUDP with default arguments (IP=127.0.0.1 Port=10001)]
> MyoUdp.exe 

[Launch MyoUDP with custom address and port]

> MyoUdp.exe 192.168.1.100 10001





Revisions:

1/18/2016 Armiger: Created
