#!/usr/bin/env python3
""" Usage:

    1) tune a freq and record MPEG-TS to default (/dev/dvb/adapter0/dvr0)

        dvbv5-zap -c tdt/canales_tdt.conf -P "Radio Clasica HQ RNE" -r


    2) record about 10 sec to a .ts file

        timeout 10 cat /dev/dvb/adapter0/dvr0 > mux.ts


    3) analyze mux.ts

        python3 bin/dvb_analyze_json.py  mux.ts -o mux.json
"""

import sys
import struct
from collections import defaultdict, Counter


TS_PACKET_SIZE = 188


# ============================================================
# MPEG / DVB tables
# ============================================================

STREAM_TYPES = {
    0x01: "MPEG-1 Video",
    0x02: "MPEG-2 Video",
    0x03: "MPEG-1 Audio",
    0x04: "MPEG-2 Audio",
    0x05: "Private Sections",
    0x06: "PES Private Data",
    0x0F: "AAC ADTS",
    0x10: "MPEG-4 Visual",
    0x11: "AAC LATM",
    0x12: "MPEG-4 SL",
    0x1B: "H.264 / AVC",
    0x24: "H.265 / HEVC",
    0x42: "AVS",
    0x81: "AC-3",
    0x87: "E-AC-3",
}


# Service names from the SDT.
# We obtain these from the TS, not from a hardcoded list.


DESCRIPTOR_NAMES = {
    0x02: "video_stream_descriptor",
    0x03: "audio_stream_descriptor",
    0x05: "registration_descriptor",
    0x06: "data_stream_alignment_descriptor",
    0x09: "CA_descriptor",
    0x0A: "ISO_639_language_descriptor",
    0x48: "service_descriptor",
    0x4D: "short_event_descriptor",
    0x52: "stream_identifier_descriptor",
    0x56: "teletext_descriptor",
    0x59: "subtitling_descriptor",
    0x66: "data_broadcast_id_descriptor",
    0x6A: "AC-3_descriptor",
    0x6F: "application_signalling_descriptor",
    0x7A: "enhanced_AC-3_descriptor",
    0x7C: "AAC_descriptor",
}


# ============================================================
# MPEG CRC
# ============================================================

def crc32_mpeg(data):

    crc = 0xFFFFFFFF

    for byte in data:

        crc ^= byte << 24

        for _ in range(8):

            if crc & 0x80000000:
                crc = (
                    (crc << 1) ^
                    0x04C11DB7
                ) & 0xFFFFFFFF
            else:
                crc = (
                    crc << 1
                ) & 0xFFFFFFFF

    return crc


# ============================================================
# Descriptor parser
# ============================================================

def parse_descriptors(data):

    result = []

    pos = 0

    while pos + 2 <= len(data):

        tag = data[pos]
        length = data[pos + 1]

        if pos + 2 + length > len(data):
            break

        value = data[
            pos + 2:
            pos + 2 + length
        ]

        pos += 2 + length

        d = {
            "tag": tag,
            "name": DESCRIPTOR_NAMES.get(
                tag,
                f"unknown_0x{tag:02X}"
            ),
            "value": value,
        }

        # ----------------------------------------------------
        # registration_descriptor
        # ----------------------------------------------------

        if tag == 0x05 and len(value) >= 4:

            d["registration"] = value[:4].decode(
                "ascii",
                errors="replace"
            )

        # ----------------------------------------------------
        # ISO 639
        # ----------------------------------------------------

        elif tag == 0x0A:

            languages = []

            for p in range(
                0,
                len(value) - 3,
                4
            ):

                lang = value[
                    p:p + 3
                ].decode(
                    "ascii",
                    errors="replace"
                )

                audio_type = value[p + 3]

                languages.append(
                    (lang, audio_type)
                )

            d["languages"] = languages

        # ----------------------------------------------------
        # service_descriptor
        #
        # tag 0x48
        #
        # service_type
        # provider_name_length
        # provider_name
        # service_name_length
        # service_name
        # ----------------------------------------------------

        elif tag == 0x48 and len(value) >= 3:

            service_type = value[0]

            p = 1

            if p >= len(value):
                continue

            provider_len = value[p]
            p += 1

            provider = value[
                p:p + provider_len
            ].decode(
                "utf-8",
                errors="replace"
            )

            p += provider_len

            if p >= len(value):
                continue

            service_len = value[p]
            p += 1

            service_name = value[
                p:p + service_len
            ].decode(
                "utf-8",
                errors="replace"
            )

            d["service_type"] = service_type
            d["provider"] = provider
            d["service_name"] = service_name

        # ----------------------------------------------------
        # AC-3
        # ----------------------------------------------------

        elif tag == 0x6A:

            d["codec"] = "AC-3"

        # ----------------------------------------------------
        # E-AC-3
        # ----------------------------------------------------

        elif tag == 0x7A:

            d["codec"] = "E-AC-3"

        # ----------------------------------------------------
        # AAC
        # ----------------------------------------------------

        elif tag == 0x7C:

            d["codec"] = "AAC"

        # ----------------------------------------------------
        # Teletext
        # ----------------------------------------------------

        elif tag == 0x56:

            entries = []

            for p in range(
                0,
                len(value) - 4,
                5
            ):

                lang = value[
                    p:p + 3
                ].decode(
                    "ascii",
                    errors="replace"
                )

                b = value[p + 3]

                teletext_type = (
                    b >> 3
                ) & 0x1F

                magazine = b & 0x07

                page = value[p + 4]

                entries.append({
                    "language": lang,
                    "type": teletext_type,
                    "magazine": magazine,
                    "page": page,
                })

            d["teletext"] = entries

        # ----------------------------------------------------
        # DVB subtitles
        # ----------------------------------------------------

        elif tag == 0x59:

            entries = []

            for p in range(
                0,
                len(value) - 7,
                8
            ):

                lang = value[
                    p:p + 3
                ].decode(
                    "ascii",
                    errors="replace"
                )

                subtitling_type = value[p + 3]

                composition_page = (
                    (value[p + 4] << 8) |
                    value[p + 5]
                )

                ancillary_page = (
                    (value[p + 6] << 8) |
                    value[p + 7]
                )

                entries.append({
                    "language": lang,
                    "type": subtitling_type,
                    "composition_page":
                        composition_page,
                    "ancillary_page":
                        ancillary_page,
                })

            d["subtitles"] = entries

        result.append(d)

    return result


# ============================================================
# TS packet iterator
# ============================================================

def ts_packets(filename):

    with open(filename, "rb") as f:

        while True:

            packet = f.read(
                TS_PACKET_SIZE
            )

            if len(packet) != TS_PACKET_SIZE:
                break

            if packet[0] != 0x47:
                continue

            yield packet


# ============================================================
# Extract PSI/SI sections from a PID
# ============================================================

def sections(filename, wanted_pid):

    buffer = bytearray()

    for packet in ts_packets(filename):

        pid = (
            ((packet[1] & 0x1F) << 8) |
            packet[2]
        )

        if pid != wanted_pid:
            continue

        adaptation_control = (
            packet[3] >> 4
        ) & 0x03

        if adaptation_control in (0, 2):
            continue

        offset = 4

        if adaptation_control == 3:

            adaptation_length = packet[4]

            offset += (
                1 +
                adaptation_length
            )

        if offset >= TS_PACKET_SIZE:
            continue

        payload = packet[offset:]

        pusi = bool(
            packet[1] & 0x40
        )

        if pusi:

            if not payload:
                continue

            pointer = payload[0]

            payload = payload[1:]

            if pointer:

                buffer.extend(
                    payload[:pointer]
                )

                while len(buffer) >= 3:

                    length = (
                        ((buffer[1] & 0x0F) << 8) |
                        buffer[2]
                    )

                    total = 3 + length

                    if len(buffer) < total:
                        break

                    yield bytes(
                        buffer[:total]
                    )

                    del buffer[:total]

            payload = payload[pointer:]

            buffer = bytearray()

        buffer.extend(payload)

        while len(buffer) >= 3:

            length = (
                ((buffer[1] & 0x0F) << 8) |
                buffer[2]
            )

            total = 3 + length

            if len(buffer) < total:
                break

            yield bytes(
                buffer[:total]
            )

            del buffer[:total]


# ============================================================
# PAT
# ============================================================

def parse_pat(section):

    programs = {}

    if len(section) < 12:
        return programs

    if section[0] != 0x00:
        return programs

    section_length = (
        ((section[1] & 0x0F) << 8) |
        section[2]
    )

    end = 3 + section_length - 4

    pos = 8

    while pos + 4 <= end:

        service_id = (
            (section[pos] << 8) |
            section[pos + 1]
        )

        pid = (
            ((section[pos + 2] & 0x1F) << 8) |
            section[pos + 3]
        )

        if service_id != 0:

            programs[service_id] = pid

        pos += 4

    return programs


# ============================================================
# PMT
# ============================================================

def parse_pmt(section):

    if len(section) < 16:
        return None

    if section[0] != 0x02:
        return None

    section_length = (
        ((section[1] & 0x0F) << 8) |
        section[2]
    )

    end = 3 + section_length - 4

    service_id = (
        (section[3] << 8) |
        section[4]
    )

    pcr_pid = (
        ((section[8] & 0x1F) << 8) |
        section[9]
    )

    program_info_length = (
        ((section[10] & 0x0F) << 8) |
        section[11]
    )

    program_descriptors = parse_descriptors(
        section[
            12:
            12 + program_info_length
        ]
    )

    pos = (
        12 +
        program_info_length
    )

    streams = []

    while pos + 5 <= end:

        stream_type = section[pos]

        pid = (
            ((section[pos + 1] & 0x1F) << 8) |
            section[pos + 2]
        )

        es_info_length = (
            ((section[pos + 3] & 0x0F) << 8) |
            section[pos + 4]
        )

        descriptors = parse_descriptors(
            section[
                pos + 5:
                pos + 5 + es_info_length
            ]
        )

        streams.append({
            "pid": pid,
            "stream_type": stream_type,
            "descriptors": descriptors,
        })

        pos += (
            5 +
            es_info_length
        )

    return {
        "service_id": service_id,
        "pcr_pid": pcr_pid,
        "program_descriptors":
            program_descriptors,
        "streams": streams,
    }


# ============================================================
# SDT
# PID 0x0011
# ============================================================

def parse_sdt(section):

    services = {}

    if len(section) < 12:
        return services

    # Actual TS SDT
    if section[0] not in (0x42, 0x46):
        return services

    section_length = (
        ((section[1] & 0x0F) << 8) |
        section[2]
    )

    end = 3 + section_length - 4

    transport_stream_id = (
        (section[3] << 8) |
        section[4]
    )

    pos = 11

    while pos + 5 <= end:

        service_id = (
            (section[pos] << 8) |
            section[pos + 1]
        )

        # EIT_schedule_flag, EIT_present_following_flag
        # running_status, free_CA_mode
        flags = (
            (section[pos + 3] << 8) |
            section[pos + 4]
        )

        descriptors_loop_length = (
            ((section[pos + 3] & 0x0F) << 8) |
            section[pos + 4]
        )

        descriptor_start = pos + 5
        descriptor_end = (
            descriptor_start +
            descriptors_loop_length
        )

        descs = parse_descriptors(
            section[
                descriptor_start:
                descriptor_end
            ]
        )

        service_name = None
        provider = None

        for d in descs:

            if d["tag"] == 0x48:

                service_name = d.get(
                    "service_name"
                )

                provider = d.get(
                    "provider"
                )

        services[service_id] = {
            "name": service_name,
            "provider": provider,
            "transport_stream_id":
                transport_stream_id,
        }

        pos = descriptor_end

    return services


# ============================================================
# PES extraction
# ============================================================

def extract_pes(filename, wanted_pid):

    pes = bytearray()
    collecting = False

    for packet in ts_packets(filename):

        pid = (
            ((packet[1] & 0x1F) << 8) |
            packet[2]
        )

        if pid != wanted_pid:
            continue

        adaptation_control = (
            packet[3] >> 4
        ) & 0x03

        if adaptation_control in (0, 2):
            continue

        offset = 4

        if adaptation_control == 3:

            adaptation_length = packet[4]

            offset += (
                1 +
                adaptation_length
            )

        if offset >= TS_PACKET_SIZE:
            continue

        payload = packet[offset:]

        pusi = bool(
            packet[1] & 0x40
        )

        if pusi:

            if collecting and pes:
                yield bytes(pes)

            pes = bytearray(
                payload
            )

            collecting = True

        elif collecting:

            pes.extend(payload)

    if collecting and pes:
        yield bytes(pes)


# ============================================================
# PES payload
# ============================================================

def pes_payload(pes):

    if len(pes) < 9:
        return b""

    if pes[0:3] != b"\x00\x00\x01":
        return b""

    stream_id = pes[3]

    # PES packet length
    pes_length = (
        (pes[4] << 8) |
        pes[5]
    )

    # MPEG-2 PES header
    if len(pes) < 9:
        return b""

    header_length = pes[8]

    payload_start = (
        9 +
        header_length
    )

    if payload_start > len(pes):
        return b""

    return pes[payload_start:]


# ============================================================
# MPEG Audio Layer II frame parser
# ============================================================

MPEG_SAMPLE_RATES = {
    0: 44100,
    1: 48000,
    2: 32000,
}


MPEG_BITRATES_L2 = {
    0: None,
    1: 32,
    2: 48,
    3: 56,
    4: 64,
    5: 80,
    6: 96,
    7: 112,
    8: 128,
    9: 160,
    10: 192,
    11: 224,
    12: 256,
    13: 320,
    14: 384,
    15: None,
}


def parse_mp2_frames(data, max_frames=1000):

    frames = []

    i = 0

    while i + 4 <= len(data):

        # MPEG audio sync
        if data[i] != 0xFF:
            i += 1
            continue

        if (data[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue

        b1 = data[i + 1]
        b2 = data[i + 2]

        version = (
            b1 >> 3
        ) & 0x03

        layer = (
            b1 >> 1
        ) & 0x03

        bitrate_index = (
            b2 >> 4
        ) & 0x0F

        sample_index = (
            b2 >> 2
        ) & 0x03

        padding = (
            b2 >> 1
        ) & 0x01

        channel_mode = (
            data[i + 3] >> 6
        ) & 0x03

        # Layer II
        if layer != 2:
            i += 1
            continue

        bitrate = (
            MPEG_BITRATES_L2
            .get(bitrate_index)
        )

        sample_rate = (
            MPEG_SAMPLE_RATES
            .get(sample_index)
        )

        if bitrate is None or sample_rate is None:
            i += 1
            continue

        # MPEG-1 Layer II
        if version == 3:
            frame_length = (
                144000 *
                bitrate //
                sample_rate
            ) + padding

        else:
            frame_length = (
                72000 *
                bitrate //
                sample_rate
            ) + padding

        if frame_length < 4:
            i += 1
            continue

        if i + frame_length > len(data):
            break

        channels = (
            1
            if channel_mode == 3
            else 2
        )

        frames.append({
            "codec": "MPEG-1 Layer II",
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels,
            "frame_length": frame_length,
        })

        i += frame_length

        if len(frames) >= max_frames:
            break

    return frames


# ============================================================
# AC-3 / E-AC-3 parser
# ============================================================

AC3_SAMPLE_RATES = {
    0: 48000,
    1: 44100,
    2: 32000,
}


AC3_BITRATES = [
    32, 40, 48, 56,
    64, 80, 96, 112,
    128, 160, 192, 224,
    256, 320, 384, 448,
    512, 576, 640,
]


AC3_CHANNELS = {
    0: 2,
    1: 1,
    2: 2,
    3: 3,
    4: 3,
    5: 4,
    6: 4,
    7: 5,
}


def parse_ac3_frames(data, max_frames=1000):

    frames = []

    i = 0

    while i + 8 <= len(data):

        # AC-3 / E-AC-3 syncword
        if data[i] != 0x0B or data[i + 1] != 0x77:
            i += 1
            continue

        # ----------------------------------------------------
        # AC-3 / E-AC-3 identification
        #
        # bsid is located after syncword.
        # We inspect both possibilities.
        # ----------------------------------------------------

        # Need at least first 8 bytes
        if i + 8 > len(data):
            break

        # fscod
        fscod = (
            data[i + 4] >> 6
        ) & 0x03

        # bsid for AC-3/E-AC-3 is around this region.
        # For practical detection, first try E-AC-3 fields.
        strmtyp = (
            data[i + 2] >> 6
        ) & 0x03

        substreamid = (
            data[i + 2] >> 3
        ) & 0x07

        # E-AC-3 has a different header layout.
        # data rate / frame size fields:
        if fscod == 3:

            # E-AC-3 uses fscod2
            fscod2 = (
                data[i + 4] >> 6
            ) & 0x03

            if fscod2 == 3:
                i += 1
                continue

        # We can distinguish E-AC-3 reliably in
        # the common DVB case by examining bsid.
        #
        # bsid is a 5-bit field beginning at bit 40
        # for the AC-3 bitstream.

        bitpos = (
            (data[i + 5] << 16) |
            (data[i + 6] << 8) |
            data[i + 7]
        )

        # fallback: use sync + DVB signaling if necessary
        # and inspect likely bsid locations.

        bsid_candidates = []

        for shift in range(0, 8):

            value = (
                (data[i + 5] << 16) |
                (data[i + 6] << 8) |
                data[i + 7]
            )

            bsid_candidates.append(
                (value >> shift) & 0x1F
            )

        # A practical DVB distinction:
        # AC-3 bsid normally <= 8
        # E-AC-3 bsid normally 11-16.
        bsid = None

        for candidate in bsid_candidates:

            if 11 <= candidate <= 16:
                bsid = candidate
                break

        if bsid is None:

            for candidate in bsid_candidates:

                if 0 <= candidate <= 8:
                    bsid = candidate
                    break

        # ----------------------------------------------------
        # More robust E-AC-3 frame parsing
        # ----------------------------------------------------

        # E-AC-3:
        #
        # syncword
        # strmtyp
        # substreamid
        # frmsiz
        # fscod
        # numblkscod
        # acmod
        # lfeon
        #
        # The following bit reader is used.

        bits = []

        for byte in data[
            i:i + 16
        ]:

            for n in range(8):

                bits.append(
                    (byte >> (7 - n)) & 1
                )

        def getbits(pos, n):

            value = 0

            for k in range(n):

                value = (
                    (value << 1) |
                    bits[pos + k]
                )

            return value

        try:

            # skip syncword
            p = 16

            strmtyp = getbits(p, 2)
            p += 2

            substreamid = getbits(p, 3)
            p += 3

            frmsiz = getbits(p, 11)
            p += 11

            fscod = getbits(p, 2)
            p += 2

            if fscod == 3:

                fscod2 = getbits(p, 2)
                p += 2

                sample_rates = {
                    0: 24000,
                    1: 22050,
                    2: 16000,
                }

                sample_rate = sample_rates.get(
                    fscod2
                )

                numblkscod = 3

            else:

                sample_rate = AC3_SAMPLE_RATES.get(
                    fscod
                )

                numblkscod = getbits(p, 2)
                p += 2

            acmod = getbits(p, 3)
            p += 3

            lfeon = getbits(p, 1)

            # E-AC-3 frame size is (frmsiz + 1) * 2
            frame_size = (
                (frmsiz + 1) * 2
            )

            if frame_size < 16:
                i += 1
                continue

            if i + frame_size > len(data):
                break

            bitrate = None

            # E-AC-3 effective bitrate
            if sample_rate:
                num_blocks = {
                    0: 1,
                    1: 2,
                    2: 3,
                    3: 6,
                }.get(numblkscod, 6)

                samples = (
                    num_blocks * 256
                )

                bitrate = int(
                    frame_size *
                    8 *
                    sample_rate /
                    samples
                )

            channels = AC3_CHANNELS.get(
                acmod,
                2
            )

            if lfeon:
                channels += 1

            # A normal E-AC-3 frame has bsid
            # 11 or higher. If the frame is valid,
            # identify it as E-AC-3.

            frames.append({
                "codec": "E-AC-3",
                "sample_rate": sample_rate,
                "channels": channels,
                "frame_size": frame_size,
                "bitrate": bitrate,
                "strmtyp": strmtyp,
                "substreamid":
                    substreamid,
                "numblkscod":
                    numblkscod,
                "acmod": acmod,
                "lfe": bool(lfeon),
            })

            i += frame_size

            if len(frames) >= max_frames:
                break

        except (IndexError, ValueError):

            i += 1

    return frames


# ============================================================
# Detect actual audio frames
# ============================================================

def analyze_audio_pid(
    filename,
    pid,
    stream_type,
    descriptors,
):

    # Read a limited number of PES packets.
    # We only need enough data to identify
    # several dozen frames.

    payload = bytearray()

    for pes in extract_pes(
        filename,
        pid
    ):

        p = pes_payload(pes)

        if p:
            payload.extend(p)

        if len(payload) >= 2_000_000:
            break

    if not payload:

        return {
            "detected": "no audio payload"
        }

    # --------------------------------------------------------
    # MPEG Audio
    # --------------------------------------------------------

    if stream_type in (0x03, 0x04):

        frames = parse_mp2_frames(
            payload
        )

        if frames:

            return summarize_frames(
                frames
            )

    # --------------------------------------------------------
    # E-AC-3 / AC-3
    # --------------------------------------------------------

    if stream_type in (
        0x06,
        0x81,
        0x87
    ):

        frames = parse_ac3_frames(
            payload
        )

        if frames:

            return summarize_frames(
                frames
            )

    # --------------------------------------------------------
    # AAC ADTS
    # --------------------------------------------------------

    if stream_type == 0x0F:

        result = detect_aac_adts(
            payload
        )

        if result:
            return result

    # --------------------------------------------------------
    # Unknown/private
    # --------------------------------------------------------

    return {
        "detected":
            "audio frames not detected",
        "payload_bytes":
            len(payload),
    }


# ============================================================
# AAC ADTS
# ============================================================

AAC_SAMPLE_RATES = {
    0: 96000,
    1: 88200,
    2: 64000,
    3: 48000,
    4: 44100,
    5: 32000,
    6: 24000,
    7: 22050,
    8: 16000,
    9: 12000,
    10: 11025,
    11: 8000,
}


def detect_aac_adts(data):

    for i in range(
        len(data) - 7
    ):

        if data[i] != 0xFF:
            continue

        if (
            data[i + 1] & 0xF6
        ) != 0xF0:

            continue

        protection_absent = (
            data[i + 1] & 1
        )

        profile = (
            (data[i + 2] >> 6)
            & 0x03
        )

        sample_index = (
            (data[i + 2] >> 2)
            & 0x0F
        )

        channel_config = (
            ((data[i + 2] & 1) << 2) |
            ((data[i + 3] >> 6) & 3)
        )

        sample_rate = AAC_SAMPLE_RATES.get(
            sample_index
        )

        if sample_rate is None:
            continue

        channels = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
            7: 8,
        }.get(
            channel_config
        )

        return {
            "detected": "AAC ADTS",
            "sample_rate": sample_rate,
            "channels": channels,
            "profile": profile + 1,
        }

    return None


# ============================================================
# Summarize frame parameters
# ============================================================

def summarize_frames(frames):

    if not frames:
        return {
            "detected":
                "no valid frames"
        }

    def values(key):

        return Counter(
            f.get(key)
            for f in frames
            if f.get(key) is not None
        )

    result = {
        "detected":
            frames[0]["codec"],
        "frames":
            len(frames),
    }

    for key in (
        "sample_rate",
        "channels",
        "bitrate",
        "frame_size",
    ):

        c = values(key)

        if c:
            result[key] = c.most_common(3)

    if "lfe" in frames[0]:

        result["lfe"] = Counter(
            f["lfe"]
            for f in frames
        ).most_common()

    return result


# ============================================================
# Main
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            f"Uso: {sys.argv[0]} mux.ts"
        )

        sys.exit(1)

    filename = sys.argv[1]

    print()
    print("=" * 78)
    print("DVB MPEG-TS ANALYZER")
    print("=" * 78)
    print()
    print(f"Fichero: {filename}")
    print()

    # --------------------------------------------------------
    # PAT
    # --------------------------------------------------------

    programs = {}

    for section in sections(
        filename,
        0
    ):

        if crc32_mpeg(section) != 0:
            continue

        programs.update(
            parse_pat(section)
        )

    if not programs:

        print("ERROR: no se encontró PAT.")
        return

    # --------------------------------------------------------
    # SDT
    # --------------------------------------------------------

    services = {}

    for section in sections(
        filename,
        0x0011
    ):

        if crc32_mpeg(section) != 0:
            continue

        services.update(
            parse_sdt(section)
        )

    # --------------------------------------------------------
    # Print services
    # --------------------------------------------------------

    print("=" * 78)
    print("SERVICIOS")
    print("=" * 78)
    print()

    for service_id in sorted(
        programs
    ):

        pmt_pid = programs[
            service_id
        ]

        service = services.get(
            service_id,
            {}
        )

        name = service.get(
            "name"
        )

        provider = service.get(
            "provider"
        )

        if not name:
            name = "(nombre no encontrado)"

        print(
            f"SERVICE_ID {service_id}"
        )

        print(
            f"  Nombre: {name}"
        )

        if provider:
            print(
                f"  Provider: {provider}"
            )

        print(
            f"  PMT PID: {pmt_pid} "
            f"(0x{pmt_pid:04X})"
        )

        print()

    # --------------------------------------------------------
    # PMTs
    # --------------------------------------------------------

    print("=" * 78)
    print("COMPONENTES / PMT / AUDIO REAL")
    print("=" * 78)

    for service_id in sorted(
        programs
    ):

        pmt_pid = programs[
            service_id
        ]

        service = services.get(
            service_id,
            {}
        )

        service_name = service.get(
            "name",
            "(nombre no encontrado)"
        )

        pmt = None

        for section in sections(
            filename,
            pmt_pid
        ):

            if crc32_mpeg(section) != 0:
                continue

            pmt = parse_pmt(
                section
            )

            if pmt:
                break

        if not pmt:
            continue

        print()
        print("-" * 78)

        print(
            f"SERVICE_ID {service_id} "
            f"→ {service_name}"
        )

        print(
            f"PMT PID {pmt_pid} "
            f"(0x{pmt_pid:04X})"
        )

        print(
            f"PCR PID {pmt['pcr_pid']} "
            f"(0x{pmt['pcr_pid']:04X})"
        )

        print()

        for stream in pmt[
            "streams"
        ]:

            pid = stream["pid"]
            st = stream["stream_type"]

            description = STREAM_TYPES.get(
                st,
                f"Unknown 0x{st:02X}"
            )

            print(
                f"PID {pid:5d} "
                f"(0x{pid:04X})"
            )

            print(
                f"  stream_type: "
                f"0x{st:02X} "
                f"({description})"
            )

            descriptors = stream[
                "descriptors"
            ]

            # ------------------------------------------------
            # Signaling
            # ------------------------------------------------

            codec_signal = None
            languages = []

            for d in descriptors:

                if "codec" in d:
                    codec_signal = d[
                        "codec"
                    ]

                for lang, audio_type in d.get(
                    "languages",
                    []
                ):

                    languages.append(
                        lang
                    )

            if codec_signal:

                print(
                    f"  señalización: "
                    f"{codec_signal}"
                )

            if languages:

                print(
                    f"  idiomas: "
                    f"{', '.join(languages)}"
                )

            # ------------------------------------------------
            # Descriptors
            # ------------------------------------------------

            for d in descriptors:

                tag = d["tag"]

                print(
                    f"  descriptor "
                    f"0x{tag:02X}: "
                    f"{d['name']}"
                )

                if "registration" in d:

                    print(
                        f"    registration: "
                        f"{d['registration']}"
                    )

            # ------------------------------------------------
            # Actual audio analysis
            # ------------------------------------------------

            if (
                st in
                (0x03, 0x04, 0x06, 0x0F,
                 0x11, 0x81, 0x87)
                or codec_signal in
                ("AC-3", "E-AC-3", "AAC")
            ):

                print(
                    "  analizando PES..."
                )

                actual = analyze_audio_pid(
                    filename,
                    pid,
                    st,
                    descriptors
                )

                for key, value in actual.items():

                    if key == "detected":

                        print(
                            f"  AUDIO REAL: "
                            f"{value}"
                        )

                    else:

                        print(
                            f"    {key}: "
                            f"{value}"
                        )

            print()


if __name__ == "__main__":
    main()
