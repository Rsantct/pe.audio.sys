## Wake On Lan

If you have a 24x7 Raspberry Pi kind of micro PC running at home, you may want to remotely WakeOnLan your main pe.audio.sys PC system.

To do so you can either:
  
- Use some smartphone app with WOL capability
- Use the provided auxiliary web page



On your 24x7 micro PC you'll need:
  
- Enable the wol section under `/etc/apache2/sites-available/pe.sudio.sys.conf`, `sudo service apache2 restart`
- Configure the MAC address of your main pe.audio.sys PC system inside `scripts/wolservice/wolservice.cfg`
- Include `- wolserver.py` inside the `scripts:` section from `config.yml` (1)

(1) If your microPC does not run pe.audio.sys, you can simply run the server by yourself:

    python3 pe.audio.sys/share/scripts/wolserver.py 1>/dev/null 2>&1 &

Then, simply bookmark `http://microPC_IP:8081` on your favourite smartphone or tablet web browser.

