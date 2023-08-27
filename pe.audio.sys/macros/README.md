# Macros
This folder is intended for general purpose user macro scripts, for example for automation tasks,
to go to listen to radio presets, etc...

**(i) The control web page will find here macro files:**

Any file here named like **`NN_some_nice_name`** ( `NN` >= 01) will be consider as an user macro by the control web page, then a web button will be used to trigger the macro.

Files not named this way, will be ignored from the control web page.

NN determines the position into the web macros key pad.

An example:

```
$ ls -1 pe.audio.sys/macros/
1_RNE
2_R.Clasica
6_flat sound
README.md
```

Will show the following key pad layout:

```
    [     RNE     ]  [  R.Clasica  ]  [     --     ]
    [     --      ]  [     --      ]  [ flat sound ]
```

# Recommended web control page behavior

The main input selector can become an user's macro manager instead of a classical preamp input selector, by just setting one option inside `config.yml`, see more details under the **[share/www](../share/www#configure-the-web-page-behavior)** folder.

This way, your web control page will be simplified, then your system becomes more user friendly than the former HiFi look.

If so, it is recommended that **you plan a complete set of macro files** in order to easily play your favourite music programs, alongside the required audio settings (e.g. type of filtering, loudness reference level, pausing the previous player, etc)

Have a look inside the **`macros/examples`** folder.

**Classical vs simplified look:**

In this example several macros will tune your favourite Radio Stations. 'Jazz' and 'RockSinfonico' will run MPD playlists from your favourite music database.

<a href="url"><img src="../doc/images/web%20inputs%20selector%20and%20macros%20buttons.png" align="center" width="480" ></a>
<a href="url"><img src="../doc/images/web%20macros%20selector.png" align="center" width="480" ></a>
