#!/usr/bin/env python3

# Copyright (c) 2006 Roberto Ripio
# This file is part of 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'FIRtro' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'FIRtro is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.


from numpy import *

def HouseCurve (f, f_corner, house_atten):
    # Corner rounding interval in octaves
    round_interval = 1
    # Scale factor for circular corner bending
    scale_factor = 10
    # Reference frequency for house curve attenuation
    f_max = 20000
    house_atten = house_atten / scale_factor
    
    f_log = log(f)
    f_corner_log = log(f_corner)
    f_max_log = log(f_max)
    f1_log = log(f_corner / 2**round_interval)
    f1_dist = f_corner_log - f1_log
    ang = arctan(house_atten / (f_max_log - f_corner_log))
    f2_log = f_corner_log + (f1_dist * cos(ang))
    y_center = -(f1_dist / tan(ang/2))
    x_center = f1_log
    
    range_1 = extract(f_log < f1_log, f_log)
    range_2 = extract(logical_and(f_log >= f1_log, f_log < f2_log) , f_log)
    range_3 = extract(f_log >= f2_log, f_log)
    
    resp_1 = zeros(len(range_1))
    resp_2 = sqrt((y_center**2) - ((range_2 - x_center)**2)) + y_center
    resp_3 = -tan(ang) * (range_3 - f_corner_log)
    
    # print( y_center, exp(f1_log), exp(f2_log) )
    
    return scale_factor * concatenate((resp_1, resp_2, resp_3))

def RoomGain (f, gain_dB = +6):
    f1      = 120
    Q       = 0.707
    pi2     = 2 * pi
    gain    = 10 ** (gain_dB / 20)
    w1      = pi2 * f1
    w2      = w1 / gain ** 0.5
    w       = pi2 * f

    rg = ((w ** 4 + ((w1/Q)**2 - 2*w1**2) * w**2 + w1**4) / 
        (w**4 + ((w2/Q)**2 - 2*w2**2) * w**2 + w2**4)) ** 0.5
    rg_dB = 20 * log10(rg)
    rg_dB -= max(rg_dB)
    
    # room gain returns positive gains for low frequencies:
    return rg_dB + gain_dB # - max(rg_dB)
