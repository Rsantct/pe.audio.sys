This folder is intended for general purpose user macro scripts, for example for automation tasks,
to go to listen to radio presets, etc...

**(i) Also the control web page will look here:**

Any file here named like **`N_some_nice_name`** will be consider as an user macro
by the control web page, then a web button will be used to trigger the macro.

N determines the position into the web macros key pad.

For example

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

