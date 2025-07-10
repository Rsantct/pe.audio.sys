#!/usr/bin/env python3

"""
    Plot filters used in the CamillaDSP pipeline

    usage: camilladsp_plot.py  <yaml_path>  [filter_pattern]

"""

print('Loading libraries can take a while ...')
import sys
import yaml
import numpy as np
import matplotlib.pyplot    as plt
from   scipy                import signal

VERBOSE = False


class Fmt:
    BLACK           = '\033[30m'
    RED             = '\033[31m'
    GREEN           = '\033[32m'
    YELLOW          = '\033[33m'
    BLUE            = '\033[34m'
    MAGENTA         = '\033[35m'
    CYAN            = '\033[36m'
    WHITE           = '\033[37m'
    GRAY            = '\033[90m'

    BRIGHTBLACK     = '\033[90m'
    BRIGHTRED       = '\033[91m'
    BRIGHTGREEN     = '\033[92m'
    BRIGHTYELLOW    = '\033[93m'
    BRIGHTBLUE      = '\033[94m'
    BRIGHTMAGENTA   = '\033[95m'
    BRIGHTCYAN      = '\033[96m'
    BRIGHTWHITE     = '\033[97m'

    BOLD            = '\033[1m'
    UNDERLINE       = '\033[4m'
    BLINK           = '\033[5m'
    END             = '\033[0m'


def load_config(yaml_file_path):

    config = {}

    try:
        with open(yaml_file_path, 'r') as f:
            config = yaml.safe_load(f)

    except FileNotFoundError:
        print(f"Error: '{yaml_file_path}' NOT found")

    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")

    if 'filters' not in config or not isinstance(config['filters'], dict):
        print("Error: 'filters' section not found.")

    fs = 44100
    if 'devices' in config and 'samplerate' in config['devices']:
        fs = config['devices']['samplerate']
        print(f"Detected samplerate: {fs} Hz")
    else:
        print(f"'samplerate' NOT found, using default {fs} Hz")

    return config, fs


def calculate_peaking_biquad_coefficients(freq, gain_db, q, fs):
    """
    Calculate the biquad coefficients for a Peaking EQ filter.
    Based on "The Audio Equalizer Cookbook" by Robert Bristow-Johnson.

    Args:
        freq (float):       center freq in Hz
        gain_db (float):    gain in dB
        q (float):          Q factor
        fs (int):           samplerate in Hz

    Returns:
        [b0, b1, b2, a1, a2] coeficientes biquad (list)
    """

    # dB --> lineal (for peaking)
    A = 10**(gain_db / 40.0)
    omega = 2 * np.pi * freq / fs
    alpha = np.sin(omega) / (2 * q)
    cos_omega = np.cos(omega)

    b0 = 1 + alpha * A
    b1 = -2 * cos_omega
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_omega
    a2 = 1 - alpha / A

    # Normalize by a0
    b0_norm = b0 / a0
    b1_norm = b1 / a0
    b2_norm = b2 / a0
    a1_norm = a1 / a0
    a2_norm = a2 / a0

    return [b0_norm, b1_norm, b2_norm, a1_norm, a2_norm]


def prepare_plot():

    # custom Coordinate Formatter for status bar
    def custom_format_coord(x, y):
        """
        Formats the x and y coordinates for the status bar.
        """
        # You can customize the precision here (e.g., :.1f for one decimal place)
        return f'x={x:.0f}, y={y:.1f}'


    xticks      = [20, 50, 100, 200, 300, 500, 700, 1000, 2000, 3000, 4000, 5000, 7000, 10000, 20000]
    xticklabels = ['20', '50', '100', '200', '300', '500', '700', '1K', '2K', '3K', '4K', '5K', '7K', '10K', '20K']

    plt.figure(figsize=(9, 8))


    # Subplot for mag
    ax_mag = plt.subplot(2, 1, 1)
    #ax_mag.set_xlabel('Hz')
    ax_mag.set_ylabel('dB')
    ax_mag.grid(True, which="both", ls="-")
    ax_mag.semilogx()
    ax_mag.set_ylim(-40, 10)
    ax_mag.set_xlim(20, 20000)
    ax_mag.set_xticks( xticks, xticklabels )

    # Subplot for phase
    ax_pha = plt.subplot(2, 1, 2)
    #ax_pha.set_xlabel('Hz')
    ax_pha.set_ylabel('deg')
    ax_pha.grid(True, which="both", ls="-")
    ax_pha.semilogx()
    ax_pha.set_ylim(-180, 180)
    ax_pha.set_xlim(20, 20000)
    ax_pha.set_xticks( xticks, xticklabels )
    deg_yticks = [-180, -135, -90, -45, 0, 45, 90, 135, 180]
    ax_pha.set_yticks( deg_yticks )

    ax_mag.format_coord = custom_format_coord
    ax_pha.format_coord = custom_format_coord

    return ax_mag, ax_pha


def get_filter_coeffs(config):
    """ Currently only filters of type 'Peaking'
    """

    filter_coeffs = {}

    for filter_name, filter_data in config['filters'].items():
        if not isinstance(filter_data, dict):
            print(f"Advertencia: El filtro '{filter_name}' no es un diccionario. Saltando.")
            continue

        filter_type_top_level = filter_data.get('type')
        parameters = filter_data.get('parameters')

        if filter_type_top_level == 'Biquad' and isinstance(parameters, dict):

            param_type = parameters.get('type')
            coefficients = None

            if param_type == 'Peaking':
                freq = parameters.get('freq')
                gain = parameters.get('gain')
                q = parameters.get('q')

                if all(v is not None for v in [freq, gain, q]):
                    try:
                        coefficients = calculate_peaking_biquad_coefficients(freq, gain, q, fs)
                        filter_coeffs[filter_name] = (coefficients[0:3], [1.0, coefficients[3], coefficients[4]])
                        if VERBOSE:
                            print(f"'{filter_name}' (Peaking): {coefficients}")
                    except Exception as e:
                        print(f"{Fmt.RED}'{filter_name}' (Peaking): error when calculating coefficients: {e}{Fmt.END}")
                else:
                    print(f"{Fmt.RED}'{filter_name}' (Peaking): bad paramenters{Fmt.END}")

            elif param_type == 'LinkwitzTransform':
                print(f"{Fmt.RED}'{filter_name}' ({param_type}): cannot calculate coefficients{Fmt.END}")

            else:
                print(f"{Fmt.RED}'{filter_name}' ({param_type}): NOT supported{Fmt.END}")

        else:
            print(f"{Fmt.RED}Warning: Skipping filter '{filter_name}'. Expected top-level type 'Biquad' and section 'parameters'. Found type: '{filter_type_top_level}', parameters: {parameters}{Fmt.END}")

    return filter_coeffs


def get_filters_per_channel(config):

    # Parse the 'pipeline' section to group all the filters applied by channel

    filters_per_channel = { 0: [],
                            1: []
                          }

    for block in config['pipeline']:

        if block["type"] != 'Filter':
            continue

        channels    = block.get('channels', [0, 1] )
        names       = block.get('names')

        for channel in channels:
            for name in names:
                filters_per_channel[channel].append(name)

    if VERBOSE:
        print()
        print('-'*100)
        print('Filters per channel:')
        for k, v in filters_per_channel.items():
            print(f'ch {k}:', v)
        print()


    return filters_per_channel


def plot_biquad_frequency_response_per_channel(config, filter_pattern=''):
    """
    Reads filter definitions from a CamillaDSP YAML configuration,
    calculates biquad coefficients for supported filter types,
    and graphs the combined frequency response for each channel defined in the pipeline.

    Args:
        config (dict): CamillaDSP config dictionary
    """

    # Subplots for magnitude and phase
    ax_mag, ax_pha = prepare_plot()

    # Defined filters
    filter_coeffs = get_filter_coeffs(config)

    # Filters for each channel in the Pipeline
    filters_per_channel = get_filters_per_channel(config)

    # Indication of which filters are being combined
    if filter_pattern:
        ax_mag.set_title(f'Filters: {filter_pattern}')
        print(f"{Fmt.BOLD}Only filter names matching: '{filter_pattern}'{Fmt.END}")

    # Generate an array of base frequencies for all calculations
    # This ensures that all responses are calculated at the same frequency points.
    w_freqs, _ = signal.freqz([1], [1], worN=8192, fs=fs)

    # Colors for each channel
    #colors = plt.cm.get_cmap('tab10', len(filters_per_channel))
    colors = ['blue', 'red']


    lines_count = 0

    for channel_key, filter_names in filters_per_channel.items():

        # Initialize with ones for multiplication
        h_combined_channel = np.ones_like(w_freqs, dtype=complex)

        channel_label = f"Channel {channel_key}"

        if filter_pattern:
            filter_names = [x for x in filter_names if filter_pattern in x]

        print(f"{channel_label}, processing: {filter_names}")

        for fname in filter_names:

            if fname in filter_coeffs:

                b, a = filter_coeffs[fname]
                _, h_individual = signal.freqz(b, a, worN=8192, fs=fs)
                h_combined_channel *= h_individual

            else:
                print(f'{Fmt.RED}Filer name `{fname}`: coefficients not available{Fmt.END}')

        combined_magnitude_db  = 20 * np.log10(abs(h_combined_channel))
        combined_phase_degrees = np.unwrap(np.angle(h_combined_channel)) * 180 / np.pi

        #line_color = colors(lines_count) # syntax if using plt.cm.get_cmap
        line_color = colors[lines_count]

        ax_mag.plot(w_freqs, combined_magnitude_db, label=channel_label, color=line_color, linewidth=2)
        ax_pha.plot(w_freqs, combined_phase_degrees, label=channel_label, color=line_color, linewidth=2)

        lines_count += 1


    if lines_count > 0:
        ax_mag.legend(loc='lower right')
        plt.show()

    else:
        print("Nothing to plot")
        plt.close()


if __name__ == "__main__":


    yaml_path       = 'camilladsp.yml'
    filter_pattern  = ''

    if sys.argv[1:]:
        yaml_path = sys.argv[1]

        if sys.argv[2:]:
            filter_pattern = sys.argv[2]

    else:
        print(__doc__)
        sys.exit()


    print(f"trying to load YAML: `{yaml_path}`")
    config, fs = load_config(yaml_path)

    if config :
        plot_biquad_frequency_response_per_channel(config, filter_pattern)
    else:
        print('Bye.')


