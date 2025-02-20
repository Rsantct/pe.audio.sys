# Integration with the (Do NOT use with PipeWire) desktop sound server

Modern desktops uses PipeWire.

Pipewire does EMULATE a PulseAudio like API, in order to players Apps like Spotify to reach the PW desktop sound server.

PW runs as a user session service.

PW integrates a JACK EMULATION, BUT we will NOT use that feature. We want **pe.audio.sys** to be compatible with headless systems without PW, through bay our own native Jack sound server.


