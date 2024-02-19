import random
import matplotlib
matplotlib.use('TkAgg')
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
from matplotlib import pyplot as plt
from pathlib import Path

samplerate = 48828
slab.set_default_samplerate(samplerate)
data_dir = Path.cwd() / 'data'


probe_level = 75
repetitions = 1  # number of repetitions per speaker
probe_speaker_id = 23
adapter_duration = 1.0
probe_duration = 0.1
hp=200

def get_adapter_level(probe_level, repetitions=1, hp=hp):
    if not freefield.PROCESSORS.mode:
        proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                     ['RX82', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                     ['RP2', 'RP2', data_dir / 'rcx' / 'play_rec_adapter.rcx']]
        freefield.initialize('dome', device=proc_list)
    freefield.set_logger('error')
    filter = slab.Filter.band('hp', (hp))
    signal_duration = 0.1
    # ---- probe  # todo doesnt work for the first recording after initialization
    [probe_speaker] = freefield.pick_speakers(probe_speaker_id)
    probe = slab.Sound.pinknoise(duration=signal_duration, level=probe_level)
    # probe = slab.Sound.tone(duration=probe_duration, level=probe_level)  # test recording with a tone
    n_rec = probe.n_samples
    freefield.write(tag='n_probe', value=probe.n_samples, processors='RX81')
    freefield.write(tag='data_probe', value=probe.data, processors=probe_speaker.analog_proc)
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)
    freefield.write(tag='probe_onset', value=1, processors='RX81')  # set to 0 to play probe immediately
    freefield.write(tag='adapter_ch_1', value=99, processors='RP2')  # prevent adapter from playing
    freefield.write(tag='adapter_ch_2', value=99, processors='RP2')
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')
    # record probe
    recs = []
    for r in range(repetitions):
        freefield.play()
        time.sleep(probe_duration)  # wait until probe has played
        rec_l = freefield.read('datal', 'RP2', n_rec)
        rec_r = freefield.read('datar', 'RP2', n_rec)
        recs.append([rec_l[1000:], rec_r[1000:]])
    recording = slab.Binaural(numpy.mean(numpy.asarray(recs), axis=0))
    probe_rec = filter.apply(recording)
    probe_rec_level = probe_rec.level

    # start with equal levels
    adapter_level_l = adapter_level_r = probe_level

    # ---- adapter
    # generate adapter
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')
    freefield.write(tag='probe_ch', value=99, processors='RX81')  # prevent probe from playing
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')  # recording length
    for i in range(20):  # stepwise level calibration
        adapter_l = slab.Sound.pinknoise(duration=signal_duration, level=adapter_level_l)
        adapter_r = slab.Sound.pinknoise(duration=signal_duration, level=adapter_level_r)
        freefield.write(tag='n_adapter', value=adapter_l.n_samples, processors='RP2')
        freefield.write(tag='data_adapter_l', value=adapter_l.data, processors='RP2')
        freefield.write(tag='data_adapter_r', value=adapter_r.data, processors='RP2')
        n_rec = adapter_l.n_samples
        recs = []
        # record adapter
        for r in range(repetitions):
            freefield.play()
            time.sleep(adapter_duration)
            rec_l = freefield.read('datal', 'RP2', n_rec)
            rec_r = freefield.read('datar', 'RP2', n_rec)
            recs.append([rec_l[1000:], rec_r[1000:]])
        recording = slab.Binaural(numpy.mean(numpy.asarray(recs), axis=0))
        adapter_rec = filter.apply(recording)
        adapter_rec_level = adapter_rec.level
        # equalize
        equalized_adapter_level = probe_rec_level - adapter_rec_level
        adapter_level_l += equalized_adapter_level[0]
        adapter_level_r += equalized_adapter_level[1]
        print(equalized_adapter_level)
        if all(numpy.abs(equalized_adapter_level) < 0.2):
            break
    return adapter_level_l, adapter_level_r

def test_calibration(adapter_level_l, adapter_level_r, probe_level, adapter_duration, probe_duration):
    [probe_speaker] = freefield.pick_speakers(probe_speaker_id)  # todo test for different speakers
    filter = slab.Filter.band('hp', (200))
    n_adapter = int(adapter_duration * samplerate)

    # make the adapter a bit longer so the ramp won't get clipped
    adapter_duration += 0.2

    # test time and level calibration with a tone
    probe = slab.Sound.tone(duration=probe_duration, level=probe_level, frequency=4000)  # test recording with a tone
    adapter_l = slab.Sound.tone(duration=adapter_duration, level=adapter_level_l, frequency=4000)
    adapter_r = slab.Sound.tone(duration=adapter_duration, level=adapter_level_r, frequency=4000)

    # pink noise (experiment conditions)
    # probe = slab.Sound.pinknoise(duration=probe_duration, level=probe_level)
    # adapter_l = slab.Sound.pinknoise(duration=adapter_duration, level=adapter_level_l)
    # adapter_r = slab.Sound.pinknoise(duration=adapter_duration, level=adapter_level_r)

    # ramping
    # probe = probe.ramp(when='both', duration=0.005)
    # adapter_l = adapter_l.ramp(when='both', duration=0.005)
    # adapter_r = adapter_r.ramp(when='both', duration=0.005)

    # probe-adapter-cross-fading
    adapter_ramp_onset = n_adapter - int(0.005 * samplerate)
    freefield.write(tag='adapter_ramp_onset', value=adapter_ramp_onset, processors='RP2')
    # delay of probe vs adapter, plus time the sound needs to reach the eardrum
    sound_travel_delay = int(1.4 / 344 * samplerate)
    dac_delay_RX8 = 24
    dac_delay_RP2 = 30
    dac_delay = dac_delay_RX8 - dac_delay_RP2
    probe_ramp_onset = adapter_ramp_onset - sound_travel_delay - dac_delay
    freefield.write(tag='probe_onset', value=probe_ramp_onset, processors='RX81')

    # recording length
    n_rec = n_adapter + probe.n_samples + 200
    freefield.write(tag='n_rec', value=n_rec, processors='RP2')

    # probe
    freefield.write(tag='n_probe', value=probe.n_samples, processors='RX81')
    freefield.write(tag='data_probe', value=probe.data, processors=probe_speaker.analog_proc)
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)

    # adapter
    freefield.write(tag='n_adapter', value=adapter_l.n_samples, processors='RP2')
    freefield.write(tag='data_adapter_l', value=adapter_l.data, processors='RP2')
    freefield.write(tag='data_adapter_r', value=adapter_r.data, processors='RP2')
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')

    # test seperately
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')
    freefield.write(tag='probe_ch', value=99, processors=probe_speaker.analog_proc)

    # play
    freefield.play()
    time.sleep(1.1)
    # get recording RCX_files
    rec_l = freefield.read('datal', 'RP2', n_rec)
    rec_r = freefield.read('datar', 'RP2', n_rec)
    recs = [rec_l, rec_r]
    recording = slab.Binaural(numpy.asarray(recs))
    recording = filter.apply(recording)
    # plot
    recording.channel(0).waveform()
    plt.xlim(0.995, 1.01)

    recording.channel(1).waveform()
    plt.xlim(0.995, 1.005)

    f1 = plt.figure()
    f2 = plt.figure()

    plt.figure(f1.number)
    plt.plot(recording.data[:, 0])
    plt.xlim(48500, 49500)

    plt.figure(f2.number)
    plt.plot(recording.data[:, 1])
    plt.xlim(48500, 49500)
    return recording

if __name__ == "__main__":

    adapter_level_l, adapter_level_r = get_adapter_level(probe_level, repetitions=1, hp=200)

    recording = test_calibration(adapter_level_l, adapter_level_r, probe_level, adapter_duration, probe_duration)