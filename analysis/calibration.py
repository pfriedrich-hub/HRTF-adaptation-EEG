import random
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
# import matplotlib
# matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
from pathlib import Path

samplerate = 48828
slab.set_default_samplerate(samplerate)
data_dir = Path.cwd() / 'data'


probe_level = 45
repetitions = 20  # number of repetitions per speaker
probe_speaker_id = 23
adapter_duration = 1.0
probe_duration = 1.0


def get_adapter_level(probe_level, repetitions=20, hp=200):
    if not freefield.PROCESSORS.mode:
        proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                     ['RX82', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                     ['RP2', 'RP2', data_dir / 'rcx' / 'play_rec_adapter.rcx']]
        freefield.initialize('dome', device=proc_list)
    freefield.set_logger('debug')
    filter = slab.Filter.band('hp', (200))

    # ---- adapter
    # generate adapter
    adapter_level = probe_level
    adapter_n_samples = int(adapter_duration * samplerate)
    adapter = slab.Sound.pinknoise(duration=adapter_duration, level=adapter_level)
    freefield.write(tag='n_adapter', value=adapter_n_samples, processors='RP2')  # write the samplesize of the adapter to the processor
    freefield.write(tag='data_adapter', value=adapter.data, processors='RP2')
    # record adapter
    n_rec = adapter_n_samples
    probe_onset = adapter_n_samples - int(0.005 * samplerate)  # delay of probe vs adapter
    freefield.write(tag='probe_ch', value=99, processors='RX81')
    freefield.write(tag='probe_onset', value=probe_onset, processors='RX81')
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')
    recs = []
    for r in range(repetitions):
        freefield.play()
        rec_l = freefield.read('datal', 'RP2', n_rec)
        rec_r = freefield.read('datar', 'RP2', n_rec)
        recs.append([rec_l[17:], rec_r[17:]])
        time.sleep(0.1)
    recording = slab.Binaural(numpy.mean(numpy.asarray(recs), axis=0))
    adapter_recording = filter.apply(recording)
    adapter_level = adapter_recording.level

    # ---- probe
    [probe_speaker] = freefield.pick_speakers(probe_speaker_id)
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    probe = slab.Sound.pinknoise(duration=probe_duration, level=probe_level)
    freefield.write(tag='n_probe', value=probe_n_samples, processors='RX81')
    freefield.write(tag='data_probe', value=probe.data, processors=probe_speaker.analog_proc)
    # record probe
    n_rec = probe_n_samples
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)
    freefield.write(tag='probe_onset', value=0, processors='RX81')  # set to 0 to play probe immediately
    freefield.write(tag='adapter_ch_1', value=99, processors='RP2')  # set to 0 to play probe immediately
    freefield.write(tag='adapter_ch_2', value=99, processors='RP2')  # set to 0 to play probe immediately
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')
    recs = []
    for r in range(repetitions):
        freefield.play()
        rec_l = freefield.read('datal', 'RP2', n_rec)
        rec_r = freefield.read('datar', 'RP2', n_rec)
        recs.append([rec_l[260:], rec_r[260:]])
        time.sleep(0.1)
    recording = slab.Binaural(numpy.mean(numpy.asarray(recs), axis=0))
    probe_recording = filter.apply(recording)
    probe_level = probe_recording.level

    equalized_adapter_level = probe_level - adapter_level
    adapter_level += equalized_adapter_level
    return(adapter_level)

def test_calibration(adapter_level, probe_level):
    # probe-adapter-cross-fading
    both_n_samples = adapter_n_samples + probe_n_samples - int(0.005 * samplerate)
    n_rec = adapter_n_samples - int(0.005 * samplerate)  # delay of probe vs adapter
    freefield.write(tag='probe_onset', value=probe_onset, processors='RX81')
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')  # set to 0 to play probe immediately
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')  # set to 0 to play probe immediately
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')











    recs = []
    for r in range(repetitions):
        freefield.play()
        rec_l = freefield.read('datal', 'RP2', n_rec)
        rec_r = freefield.read('datar', 'RP2', n_rec)
        recs.append([rec_l[1750:], rec_r[1750:]])
        time.sleep(0.1)
    recording = slab.Binaural(numpy.mean(numpy.asarray(recs), axis=0))
    return recording

    adapter_rec_level = numpy.mean(recording.level)

