#!/usr/bin/env python3

"""
    Plot filters used in the CamillaDSP pipeline

    usage: camilladsp_plot.py  <yaml_path>  [filter_pattern] [--verbose] [--peaudiosys]

            --peaudiosys:    makes a graph to be used in pe.audio.sys web page

"""

print('Loading libraries can take a while ...')
import sys
import yaml
import numpy as np
import matplotlib.pyplot    as plt
from   scipy                import signal

from   camilladsp_plot_mod.fmt                  import Fmt
import camilladsp_plot_mod.audio_eq_cook_book   as eqbook


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


def prepare_plot():

    # custom Coordinate Formatter for status bar
    def custom_format_coord(x, y):
        """
        Formats the x and y coordinates for the status bar.
        """
        # You can customize the precision here (e.g., :.1f for one decimal place)
        return f'x={x:.0f}, y={y:.1f}'


    if PLOTSTYLE == 'pe.audio.sys':

        plt.style.use('dark_background')
        plt.rcParams.update({'font.size': 6})
        plt.rcParams['lines.linewidth'] = 3

        FREQ_LIMITS = [20, 20000]
        FREQ_TICKS  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
        FREQ_LABELS = ['20', '50', '100', '200', '500', '1K', '2K', '5K', '10K', '20K']
        DB_LIMITS   = [-20, +9]
        DB_TICKS    = [-18, -12, -6, 0, 6]
        DB_LABELS   = ['-18', '-12', '-6', '0', '6']


        fig, ax_mag = plt.subplots()
        fig.set_figwidth( 5 )   # 5 inches at 100dpi => 500px wide
        fig.set_figheight( 1.5 )
        fig.set_facecolor( WEBCOLOR )
        ax_mag.set_facecolor( WEBCOLOR )

        #ax_mag.set_xlabel('Hz')
        #ax_mag.set_ylabel('dB')
        ax_mag.grid(False)
        ax_mag.semilogx()
        ax_mag.set_ylim(DB_LIMITS)
        ax_mag.set_xlim(FREQ_LIMITS)
        ax_mag.set_xticks(FREQ_TICKS, FREQ_LABELS)
        ax_mag.set_yticks(DB_TICKS, DB_LABELS)

        # no subplot for phase
        ax_pha = None

        ax_mag.format_coord = custom_format_coord


    else:
        FREQ_LIMITS = [20, 20000]
        FREQ_TICKS  = [20, 50, 100, 200, 300, 500, 700, 1000, 2000, 3000, 4000, 5000, 7000, 10000, 20000]
        FREQ_LABELS = ['20', '50', '100', '200', '300', '500', '700', '1K', '2K', '3K', '4K', '5K', '7K', '10K', '20K']
        DB_LIMITS   = [-30, +20]
        DB_TICKS    = [-30, -20, -10, 0, 10, 20]
        DB_LABELS   = ['-30', '-20', '-10', '0', '10', '20']


        N = 1
        if PHASE:
            N = 2
            plt.figure(figsize=(9, 8))
        else:
            plt.figure(figsize=(9, 5))
            plt.subplots_adjust(top=0.80)

        # Subplot for mag
        ax_mag = plt.subplot(N, 1, 1)
        #ax_mag.set_xlabel('Hz')
        ax_mag.set_ylabel('dB')
        ax_mag.grid(True, which="both", ls="-")
        ax_mag.semilogx()
        ax_mag.set_ylim(DB_LIMITS)
        ax_mag.set_xlim(FREQ_LIMITS)
        ax_mag.set_xticks(FREQ_TICKS, FREQ_LABELS)
        ax_mag.set_yticks(DB_TICKS, DB_LABELS)
        ax_mag.format_coord = custom_format_coord

        if PHASE:
            # Subplot for phase
            ax_pha = plt.subplot(2, 1, 2)
            #ax_pha.set_xlabel('Hz')
            ax_pha.set_ylabel('deg')
            ax_pha.grid(True, which="both", ls="-")
            ax_pha.semilogx()
            ax_pha.set_ylim(-180, 180)
            ax_pha.set_xlim(FREQ_LIMITS)
            ax_pha.set_xticks(FREQ_TICKS, FREQ_LABELS)
            deg_yticks = [-180, -135, -90, -45, 0, 45, 90, 135, 180]
            ax_pha.set_yticks( deg_yticks )
            ax_pha.format_coord = custom_format_coord

        else:
            ax_pha = None

    return ax_mag, ax_pha


def get_filter_coeffs(config):
    """ Currently only filters of type
        - 'Peaking'
        - 'LinkwitzTransform'
    """

    filter_coeffs = {}


    if VERBOSE:
        print()
        print('-'*100)
        print('Filters available:')

    for filter_name, filter_data in config['filters'].items():

        if not isinstance(filter_data, dict):
            print(f"Warning: '{filter_name}' is not a valid dictionary, we discard it.")
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
                        coeffs = eqbook.peaking_biquad_coefficients(freq, gain, q, fs)

                        filter_coeffs[filter_name] = {
                            'type':     'Peaking',
                            'freq':     freq,
                            'coeffs':   coeffs
                        }

                        if VERBOSE:
                            print(filter_coeffs[filter_name])

                    except Exception as e:
                        print(f"{Fmt.RED}'{filter_name}' (Peaking): error when calculating coefficients: {e}{Fmt.END}")

                else:
                    print(f"{Fmt.RED}'{filter_name}' (Peaking): bad paramenters{Fmt.END}")

            elif param_type == 'LinkwitzTransform':

                freq_act    = parameters.get('freq_act')
                q_act       = parameters.get('q_act')
                freq_target = parameters.get('freq_target')
                q_target    = parameters.get('q_target')

                if all(v is not None for v in [freq_act, q_act, freq_target, q_target]):

                    try:
                        coeffs = eqbook.linkwitz_transform_coefficients(freq_act, q_act, freq_target, q_target, fs)

                        filter_coeffs[filter_name] = {
                            'type':     'LinkwitzTransform',
                            'freq':     freq_target,
                            'coeffs':   coeffs
                        }

                        if VERBOSE:
                            print(filter_coeffs[filter_name])

                    except Exception as e:
                        print(f"{Fmt.RED}'{filter_name}' (LinkwitzTransform): error when calculating coefficients: {e}{Fmt.END}")

                else:
                    print(f"{Fmt.RED}'{filter_name}' (LinkwitzTransform): bad paramenters{Fmt.END}")

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


    return filters_per_channel


def plot_frequency_response_per_channel(config, filter_pattern=''):
    """
    Reads filter definitions from a CamillaDSP YAML configuration,
    calculates biquad coefficients for supported filter types,
    and graphs the combined frequency response for each channel defined in the pipeline.

    Args:
        config (dict): CamillaDSP config dictionary
    """

    # Subplots for magnitude, phase, group_delay
    ax_mag, ax_pha = prepare_plot()

    # Defined filters
    filter_coeffs = get_filter_coeffs(config)

    # Filters for each channel in the Pipeline
    filters_per_channel = get_filters_per_channel(config)

    if VERBOSE:
        print()
        print('-'*100)
        print('Plotting:')

    # Indication of which filters are being combined
    if filter_pattern:
        if PLOTSTYLE == 'normal':
            ax_mag.set_title(f'Filters: {filter_pattern}')
        print(f"{Fmt.BOLD}Only filter names matching: '{filter_pattern}'{Fmt.END}")

    # Generate an array of base frequencies for all calculations
    # This ensures that all responses are calculated at the same frequency points.
    w_freqs, _ = signal.freqz([1], [1], worN=8192, fs=fs)

    # Colors for each channel
    #colors = plt.cm.get_cmap('tab10', len(filters_per_channel))
    colors = ['steelblue', 'indianred']

    lines_count = 0

    mag_annotations = []

    for channel_key, filter_names in filters_per_channel.items():

        # Initialize with ones for multiplication
        h_combined_channel = np.ones_like(w_freqs, dtype=complex)

        if PLOTSTYLE == 'pe.audio.sys':
            channel_label = {0: 'L', 1: 'R'}[lines_count]
        else:
            channel_label = f"Channel {channel_key}"

        if filter_pattern:
            filter_names = [x for x in filter_names if filter_pattern in x]

        print(f"{channel_label}, processing: {filter_names}")

        for fname in filter_names:

            if fname in filter_coeffs:

                b, a = filter_coeffs[fname]["coeffs"]
                _, h_individual = signal.freqz(b, a, worN=8192, fs=fs)
                h_combined_channel *= h_individual

                mag_annotations.append(
                    {   'xpos':     filter_coeffs[fname]["freq"],
                        'ypos':     19 - lines_count * 8,
                        'text':     str(fname) ,
                        'color':    colors[lines_count]
                    }
                )

            else:
                print(f'{Fmt.RED}Filer name `{fname}`: coefficients not available{Fmt.END}')

        combined_magnitude_db  = 20 * np.log10(abs(h_combined_channel))
        combined_phase_degrees = np.unwrap(np.angle(h_combined_channel)) * 180 / np.pi

        #line_color = colors(lines_count) # syntax if using plt.cm.get_cmap
        line_color = colors[lines_count]

        if PLOTSTYLE == 'pe.audio.sys':
            ax_mag.plot(w_freqs, combined_magnitude_db, label=channel_label, color=line_color)

        else:
            ax_mag.plot(w_freqs, combined_magnitude_db,  label=channel_label, color=line_color, linewidth=2)
            if PHASE:
                ax_pha.plot(w_freqs, combined_phase_degrees, label=channel_label, color=line_color, linewidth=2)

        lines_count += 1

    if PLOTSTYLE == 'normal':

        for i, ann in enumerate(mag_annotations):

            ax_mag.annotate(    text        = ann["text"],
                                xy          = (ann["xpos"], 0),
                                xytext      = (ann["xpos"] - 2 , ann["ypos"] + 1.5),
                                rotation    = 40,
                                fontsize    = plt.rcParams["font.size"] * 0.7,
                                color       = ann["color"]
            )
            # Add a dot
            ax_mag.plot( ann["xpos"], ann["ypos"], marker='o', markersize=3, color=ann["color"] )


    if lines_count > 0:

        if PLOTSTYLE == 'pe.audio.sys':
            ax_mag.legend( facecolor=WEBCOLOR, loc='lower right')
            fpng = f'{IMGFOLDER}/drc_{drc_set}.png'
            plt.savefig( fpng, facecolor=WEBCOLOR )

        else:
            ax_mag.legend(loc='lower right')

        plt.show()

    else:
        print("Nothing to plot")
        plt.close()


if __name__ == "__main__":

    VERBOSE = False
    PHASE = False

    PLOTSTYLE = 'normal'

    yaml_path       = 'camilladsp.yml'
    filter_pattern  = ''


    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()

    for opc in sys.argv[1:]:

        if '-v' in opc:
            VERBOSE = True

        elif '.yml' in opc:
            yaml_path = opc

        elif '-ph' in opc:
            PHASE = True

        elif '-pe' in opc:
            PLOTSTYLE = 'pe.audio.sys'
            # Same color as pe.audio.sys index.html background-color: rgb(38, 38, 38)
            WEBCOLOR    = (.15, .15, .15)
            drc_set = 'CamillaDSP'
            IMGFOLDER = '.'

        else:
            filter_pattern = opc


    print(f"trying to load YAML: `{yaml_path}`")
    config, fs = load_config(yaml_path)

    if config :
        plot_frequency_response_per_channel(config, filter_pattern)
    else:
        print('Bye.')


