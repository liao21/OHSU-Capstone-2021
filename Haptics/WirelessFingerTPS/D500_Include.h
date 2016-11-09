#ifndef PPS_D500_H
#define PPS_D500_H

#define SEN_I2C_BROADCAST 254

#ifdef _PPS_D500_API_BUILD_
#define D500_API_DECLARE	extern "C" __declspec(dllexport)
#else
#define D500_API_DECLARE	extern "C" __declspec(dllimport)
#endif

//Thread Controls
D500_API_DECLARE bool getData(float* data, int & framesReceived, int framesRequested);
D500_API_DECLARE bool getConfig(int *devices, int &nDevices);
D500_API_DECLARE bool setDAQEnabled(bool isEnabled);
D500_API_DECLARE bool configureD500(char AverageLength, char dacCurrent, char scanCount);
D500_API_DECLARE void D500_reset(void);

//D500 Functions

D500_API_DECLARE bool setI2CAddress(int newAddress, char i2cAddress);

D500_API_DECLARE bool startScanning(char i2cAddress);
D500_API_DECLARE bool stopScanning(char i2cAddress);

D500_API_DECLARE bool setDacCurrent(char dacCurrent, char i2cAddress, bool writetoEEPROM);
D500_API_DECLARE bool setScanCount(char scanCount, char i2cAddress, bool writetoEEPROM);
D500_API_DECLARE bool setAvgLen(int length, char i2cAddress, bool writetoEEPROM);
D500_API_DECLARE bool tare(char i2cAddress);
D500_API_DECLARE bool unTare(char i2cAddress);

//Reserved
D500_API_DECLARE bool SendData(byte * Data, unsigned char length);
D500_API_DECLARE bool CheckForData(byte * Data,unsigned char length);
D500_API_DECLARE bool SetI2CLoopDivider(int divider);  // Slows down I2C loop
D500_API_DECLARE bool StartReceiving(void);

//Not implemented
D500_API_DECLARE bool ResetEEPROM(unsigned char i2cAddress);
D500_API_DECLARE bool setCalibrationPoint(char Sensor_Num, int Point,  char i2cAddress, bool writetoEEPROM);
D500_API_DECLARE bool ClearDigitactsCalibration(char i2cAddress, bool writetoEEPROM);

#endif
