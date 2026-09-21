
## Paquetes
    sudo apt update
    sudo apt install v4l-utils dvb-tools linux-firmware


## Canales

El archivo **`es-UHF-c21-c49.conf`** contiene la banda UHF utilizada para la Televisión Digital Terrestre (TDT) tras el Segundo Dividendo Digital, desde el Canal 21 (474 MHz) hasta el Canal 48 (690 MHz).

Para escanar los servicios y obtener un archivo .conf moderno usamos **`dvbv5-scan`**, ejemplo:

    dvbv5-scan es-UHF-c21-c49.conf -o canales_tdt.conf

Para convertir `canales_tdt.conf` al formato clásico de **Mplayer**, usar el script `bin/dvbv5_channels_to_mplayer.py`

## Varias tarjetas DVB-T

Elegir la deseada en **`config.yml`**

    # Optional for more than one adapterX under /dev/dvb/
    # You can use an udev rule for a named symlink to /dev/dvb/adapterX
    dvb_adapter_id:  hauppage
