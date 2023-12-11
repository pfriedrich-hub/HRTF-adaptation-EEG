import random
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
from matplotlib import pyplot as plt
from pathlib import Path

fs = 48828
slab.set_default_samplerate(fs)

# initial test
subject_id = '1'
condition = 'Ears Free'
data_dir = Path.cwd() / 'HRTF-adaptation-EEG' / 'Experiments' / 'familiarization' / subject_id / condition

repetitions = 3  # number of repetitions per speaker


def familiarization_test(subject_id, data_dir, condition, repetitions):
    global speakers, stim, sensor, tone, file_name
    if not freefield.PROCESSORS.mode:
        freefield.initialize('dome', default='play_rec', sensor_tracking=True)
    freefield.load_equalization(Path.cwd() / 'data' / 'calibration' / 'calibration_dome_23.05')

    # generate stimulus
    bell = slab.Sound.read(Path.cwd() / 'data' / 'sounds' / 'bell.wav')
    bell.level = 75
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    adapter = slab.Sound.pinknoise(duration=1)  # playing from headphones
    probe = slab.Sound.pinknoise(duration=0.1, kind='non_repeating')
    interval = slab.Sound.silence(duration=0.35)

    channels = (19, 21, 23, 25, 27)
    seq = slab.Trialsequence(conditions=channels, n_reps=6, kind='non_repeating')
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
