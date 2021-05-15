# Using an IR infrared remote to manage pe.audio.sys

TO BE DONE ASAP

## FAQ

### IR does not work on Desktop

Some computers having an integrated IR device, needs to be disabled from X windows usage.

For example, in a Mac computer, add the following file:


`nano ~/.config/autostart/AppleIRreceiver_xdisable.desktop`

      [Desktop Entry]
      Type=Application
      Exec=xinput --disable "Apple Computer, Inc. IR Receiver"
      Hidden=false
      NoDisplay=false
      X-GNOME-Autostart-enabled=true
      Name[es_ES]=AppleIRreceiver_xdisable
      Name=AppleIRreceiver_xdisable
      Comment[es_ES]=
      Comment=


