import random
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

# initial test
subject_id = '1'
condition = 'Ears Free'
subject_dir = data_dir / 'Experiments' / 'familiarization' / subject_id / condition

repetitions = 6  # number of repetitions per speaker
target_speakers = (19, 21, 23, 25, 27)


def familiarization_test(target_speakers, repetitions):
    global probe_duration, sequence
    proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_adapter_probe.rcx'],
                 ['RX82', 'RX8', data_dir / 'rcx' / 'play_adapter_probe.rcx'],
                 ['RP2', 'RP2', data_dir / 'rcx' / 'button.rcx']]
    freefield.initialize('dome', device=proc_list, sensor_tracking=True)

    # generate random sequence of target speakers
    sequence = slab.Trialsequence(conditions=target_speakers, n_reps=repetitions, kind='non_repeating')

    # adapter
    # generate and write adapter
    adapter_duration = 1.0
    adapter = slab.Sound.pinknoise(duration=adapter_duration)  # playing from headphones
    freefield.write(tag='n_adapter', value=adapter.n_samples, processors='RX82')
    freefield.write(tag='data_adapter', value=adapter.data, processors='RX82')
    # set adapter speakers
    adapter_speaker_ids = [0, 42]
    adapter_speakers = freefield.pick_speakers(adapter_speaker_ids)
    freefield.write(tag='adapter_ch_1', value=adapter_speakers[0].analog_channel, processors='RX82')
    freefield.write(tag='adapter_ch_2', value=adapter_speakers[1].analog_channel, processors='RX82')

    # probe
    probe_duration = 0.1
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    # set probe buffer parameters
    freefield.write(tag='n_probe', value=probe_n_samples, processors='RX81')
    # probe-adapter-cross-fading
    probe_onset = adapter.n_samples - int(0.005 * samplerate)  # delay of probe vs adapter
    freefield.write(tag='probe_onset', value=probe_onset, processors='RX81')

    for trial in sequence:
        target_speaker_id = sequence.conditions[trial]
        play_trial(target_speaker_id)

    # save trialsequence

    return


def play_trial(target_speaker_id):
    # generate and write probe
    probe = slab.Sound.pinknoise(duration=probe_duration)
    freefield.write(tag='data_probe', value=probe.data, processors='RX81')
    [probe_speaker] = freefield.pick_speakers(target_speaker_id)
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)
    freefield.play()

    # while True:
    #     freefield.wait_for_button()
    #     freefield.play(kind='zBusA')

    # activate central led
    freefield.write('led', value=1, processors='RX81')
    time.sleep(1)
    # get  0 0 head pose
    calibration = freefield.calibrate_sensor()
    freefield.write('led', value=0, processors='RX81')


    # led
    if sequence.thi_n < 15:
        time.sleep()
        # turn on led with probe sound
        freefield.write('led', values=1, processors='RX81')


    # headpose
    headpose = freefield.get_head_pose()

    # response
    freefield.wait_for_button()
    freefield.write('led', values=0, processors='RX81')

    # isi
    time.sleep()







    # freefield.load_equalization(Path.cwd() / 'data' / 'calibration' / 'calibration_dome_23.05')

    # generate stimulus
    bell = slab.Sound.read(Path.cwd() / 'data' / 'sounds' / 'bell.wav')
    bell.level = 75
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)


    interval = slab.Sound.silence(duration=0.35)

    stimulus = probe.ramp(duration=0.05, when='both', level=70)
    for channels in seq:
        # write channel to rcx
        stimulus.level = probe
        stimulus.play()
    with slab.key() as key:
        response = key.getch()
        # get head position
    seq.add_response(response)
    # first 15 stimuli are accompanied by a visual cue

    stimulus.wait_to_finish_playing()
    response = 0
    while not response:
        pose = freefield.get_head_pose(method='sensor')
        if all(pose):
            print('head pose: azimuth: %.1f, elevation: %.1f' % (pose[0], pose[1]), end="\r", flush=True)
        else:
            print('no head pose detected', end="\r", flush=True)
        response = freefield.read('response', processor='RP2')
    if all(pose):
        print('Response| azimuth: %.1f, elevation: %.1f' % (pose[0], pose[1]))
    freefield.set_signal_and_speaker(signal=tone, speaker=23)
    freefield.play()
    freefield.wait_to_finish_playing()
    return numpy.array((pose, probe))

def play_trial(speaker_id):
    probe = slab.Sound.pinknoise(duration=0.1)


if name == mai
    localization_test()