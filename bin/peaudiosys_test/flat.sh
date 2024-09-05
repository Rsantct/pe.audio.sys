
# clear all audio settings:

echo -n "input none: "      && control input none

echo -n "powersave off: "   && control powersave off

echo -n "convolver on: "    && control convolver on

echo -n "level -10: "       && control level -10

echo -n "bass 0: "          && control bass 0

echo -n "treble 0: "        && control treble 0

echo -n "lu_offset 0: "     && control lu_offset 0

echo -n "loudness off: "    && control loudness off

echo -n "drc none: "        && control drc none

echo -n "target none: "     && control set_target none

echo -n "subsonic off: "    && control subsonic off

echo -n "add_delay 0: "     && control add_delay 0


# view filters
echo
peaudiosys_view_brutefir.py| grep "f\."

# and outputs delays
echo
cmd='li; lo ; quit;'
echo $cmd | nc localhost 3000 | grep "lo\.\|mi\.\|hi\.\|sw."
