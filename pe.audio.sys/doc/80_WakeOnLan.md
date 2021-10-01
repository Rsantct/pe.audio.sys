## Wake On Lan

To remotely WakeOnLan your main pe.audio.sys PC system, you can either:
  
- Use some smartphone app with WOL capability (geek option)
- Use the provided auxiliary web page (end user friendly option)

If you have a 24x7 Raspberry Pi kind of micro PC running at home, you may want to use it as a WOL server.


On your 24x7 micro PC you'll need:
  
- Enable the wol section under `/etc/apache2/sites-available/pe.sudio.sys.conf`, `sudo service apache2 restart`
- Configure the MAC address of your main pe.audio.sys PC system inside `scripts/wolservice/wolservice.cfg`
- Include `- wolserver.py` inside the `scripts:` section from `config.yml` (1)

(1) If your microPC does not run pe.audio.sys, you can simply run the server by yourself:

    python3 pe.audio.sys/share/scripts/wolserver.py 1>/dev/null 2>&1 &

Then, simply bookmark `http://microPC_IP:8081` on your favourite smartphone or tablet web browser.

