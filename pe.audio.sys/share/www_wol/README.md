This is an optional web page to access to the optional Wake On LAN service as described at:

  **`share/scripts/wolservice/WakeOnLan.md`**

You will need to use the optional apache site configuration:


        sudo a2dissite  pe.audio.sys.conf
        sudo a2ensite   pe.audio.sys_wol.conf
        sudo service apache2 reload
  
  
