This folder is intended for general purpose user macro scripts, for example for automation tasks,
to go to listen to radio presets, etc...

**(i) The control web page will find here macro files:**

Any file here named like **`NN_some_nice_name`** ( `NN` >= 1) will be consider as an user macro by the control web page, then a web button will be used to trigger the macro.

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

### Optional web control page macros behavior

If desired, the main input selector can become an user's macro manager insteaf of a standar preamp input selector, see more details under the **`share/www`** folder.
