#ifndef _PPSDAQ_H_
#define _PPSDAQ_H_
//---------------------------------------------------------------------------
// PPSDaq.h
//
// PPS Data Acquisition API
// Copyright (c) 2008 by Pressure Profile Systems, Inc.
// All Rights Reserved
//
//---------------------------------------------------------------------------
// We need standard Windows libraries to use bool type to preserve
// compatibility with C# apps. (They can't reliably read the bool type
// via DLL calls for some strange reason.)
//
#define WIN32_LEAN_AND_MEAN      // Don't load unnecessary Windows libraries
#define NOMINMAX                 // We'll use the STL min and max
#include <windows.h>
//---------------------------------------------------------------------------
// Allows us to use the same header for building the library
// as for using it
//
#ifdef _PPS_DLL_BUILD_
#define DLL_FUNCTION extern "C" __declspec(dllexport)
#else
#define DLL_FUNCTION extern "C" __declspec(dllimport)
#endif
//---------------------------------------------------------------------------
// Variable Types
typedef float           output_t;
typedef unsigned long   time_stamp_t;
typedef char const*     string_t;
//---------------------------------------------------------------------------
// API Function Definitions

// Sets up and configures the PPS DAQ System
//
// configFile: PPS-created file specific to your setup
// returns: TRUE on success
DLL_FUNCTION bool ppsInitialize(string_t configFile);

// Begins data acquisition
//
// returns: TRUE on success
DLL_FUNCTION bool ppsStart();

// Ends data acquisition
//
// returns: TRUE on success
DLL_FUNCTION bool ppsStop();

// Retrieve the size (i.e. number of elements) in one frame
//
// returns: element count
DLL_FUNCTION int  ppsGetRecordSize();

// Retrieve the number of frames of data available for transfer
//
// returns: frame count
DLL_FUNCTION int  ppsFramesReady();

// Retrieve sensor data. The function assumes that memory has been
// pre-allocated, and regardless of how much data is requested will
// not copy more than is available at the time.
//
// nFrames: number of frames of data to copy
// times: pointer to pre-allocated memory, one timestamp per frame
// data: pointer to pre-allocated memory, (nFrames * recordSize) large
// returns: the actual number of frames of data copied
DLL_FUNCTION int  ppsGetData(int nFrames,
        time_stamp_t* times,
        output_t* data);

// Send hardware-specific commands. Available commands and formats
// are dependent on the type of hardware connected. Contact PPS for
// documentation on your specific hardware.
//
// command: C-style string with command request being sent
// args: pointer to space for return data
DLL_FUNCTION bool ppsDirectCommand(string_t command, void* args);

// For raw data, retrieve the maximum output signal for use in
// scaling data.
//
// returns: the maximum binary value available from the hardware
DLL_FUNCTION int  ppsGetMaxSignal();

// Set a new baseline value based on the current sensor readings.
// This value will be subtracted from each element when data is
// returned.
DLL_FUNCTION void ppsSetBaseline();

// Reset any baseline values to zero
DLL_FUNCTION void ppsClearBaseline();

// Check to see if output reflects calibrated or raw data
//
// returns: TRUE for calibrated data
DLL_FUNCTION bool ppsIsCalibrated();

//---------------------------------------------------------------------------
#endif
