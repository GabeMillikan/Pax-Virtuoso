# Opus Codec

"Opus" is the name of the codec that Discord uses to compress audio data.
This bot needs that codec library in order to process audio (i.e. to change the volume).

You'll need to install the codec to use the bot.

### Windows Installation

The pre-built `opus.dll` is provided in this directory so that you don't have to compile it yourself.\
Copy the DLL onto your `PATH`, such as the `venv\Scripts\opus.dll` for a virtual environment.

If you want or need to compile the library yourself:

1. download the source code from [[https://opus-codec.org/downloads/]]
2. open `win32\VS2015\opus.sln` with Visual Studio (upgrade the SDK version, if prompted)
3. compile using the `ReleaseDLL_fixed` on the appropriate architecture
4. use the produced `x64\ReleaseDLL_fixed\opus.dll` like above

### Linux/MacOS Installation

Simply use apt: `sudo apt-get install libopus0`.
If this doesn't work, you will need to compile from source and place `libopus.so.0` on your `PATH` (similar to the Windows instruction).
