## Wake On Lan

To remotely WakeOnLan your main pe.audio.sys PC system, you can either:
  
- Use some smartphone app with WOL capability (geek option)
- Use the provided auxiliary web page (end user friendly option)

If you have a 24x7 Raspberry Pi kind of Linux based micro PC running at home, you may want to use it as a WOL server.


On your 24x7 micro PC you'll need:
  
- `sudo apt install wakeonlan`
- Enable the wol section under `/etc/apache2/sites-available/pe.sudio.sys.conf`, `sudo service apache2 restart`
- Configure the MAC address of your main pe.audio.sys PC system inside `pe.audio.sys/scripts/wolservice/wolservice.cfg`
- Include `- wolserver.py` inside the `scripts:` section from `pe.audio.sys/config.yml` (1)

(1) If your microPC does not run pe.audio.sys, you can simply run the standalone server by yourself:

    python3 pe.audio.sys/share/scripts/wolserver.py 1>/dev/null 2>&1 &

Then, simply bookmark `http://microPC_IP:8081` on your favourite smartphone or tablet web browser.

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/wol_web_page.png" align="center" width="250" ></a>