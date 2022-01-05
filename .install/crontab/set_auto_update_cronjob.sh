#!/bin/sh

echo "--------------------------------------------------------------------------"

AUTOUPDATE=$( grep auto_update ~/pe.audio.sys/config/config.yml     \
                | awk -F':' '{print $2}'                            \
                | awk -F'#' '{print $1}'                            \
                | awk '{ gsub(/ /,""); print }' )


crontab -l > $HOME/tmp/curr_crontab


if [ $AUTOUPDATE = "true" ]; then

    already_updating=$( grep "update_peaudiosys.sh" $HOME/tmp/curr_crontab \
                          | grep -v ^\# )

    if [ "$already_updating" ]; then
        echo "Your crontab already has an auto-update job, nothing done."
    else
        echo "Will add a daily auto-update to your crontab."
        cat $HOME/tmp/curr_crontab $HOME/tmp/pe.audio.sys-master/.install/crontab/auto_update_cronjob \
            | crontab -
        echo "(i) Please check 'crontab -l'"
    fi

else
    echo "auto_update not enabled, will remove job from your crontab if necessary."

    cp $HOME/tmp/curr_crontab $HOME/tmp/new_crontab

    # Use this to remove exact lines matching within the auto_update_cronjob file
    #while IFS= read -r line; do
    #    grep -Fv "$line" $HOME/tmp/new_crontab > $HOME/tmp/tmp && mv $HOME/tmp/tmp $HOME/tmp/new_crontab
    #done < "$HOME/tmp/pe.audio.sys-master/.install/crontab/auto_update_cronjob"


    # or use this to remove similar lines as per the below given patterns
    p="update pe.audio.sys"
    grep -Fvi "$p" $HOME/tmp/new_crontab > $HOME/tmp/tmp && mv $HOME/tmp/tmp $HOME/tmp/new_crontab
    p="update_peaudiosys.sh --auto"
    grep -Fvi "$p" $HOME/tmp/new_crontab > $HOME/tmp/tmp && mv $HOME/tmp/tmp $HOME/tmp/new_crontab


    cat $HOME/tmp/new_crontab | crontab -
    echo "(i) Please check 'crontab -l'"

fi


rm -f $HOME/tmp/curr_crontab
rm -f $HOME/tmp/new_crontab

echo "--------------------------------------------------------------------------"
