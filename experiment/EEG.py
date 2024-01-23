import random
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
from random import randint
from matplotlib import pyplot as plt
from pathlib import Path

samplerate = 48828
slab.set_default_samplerate(samplerate)
data_dir = Path.cwd() / 'data'

# initial test
subject_id = '1'
condition = 'Ears Free'
subject_dir = data_dir / 'Experiments' / 'EEG' / subject_id / condition

repetitions = 3  # number of repetitions per speaker
target_speakers = (20, 22, 24, 26)



def familiarization_test(subject_id, data_dir, condition, repetitions):
    global speakers, stim, sensor, tone, file_name
    if not freefield.PROCESSORS.mode:
        freefield.initialize('dome', default='play_rec', sensor_tracking=True)
    freefield.load_equalization(Path.cwd() / 'data' / 'calibration' / 'calibration_dome_23.05.pkl')

    # generate stimulus
    bell = slab.Sound.read(Path.cwd() / 'data' / 'sounds' / 'bell.wav')
    bell.level = 75
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    adapter = slab.Sound.pinknoise(duration=1)   #playing from headphones
    probe = slab.Sound.pinknoise(duration=0.1, kind='non_repeating')
    probe = probe.ramp(duration=0.005, when='both')
    interval = slab.Sound.silence(duration=0.35)

    channels = (20, 22, 24, 26)
    #playing adapter from headphones
    trial_seq = slab.Trialsequence(conditions=channels, n_reps=60, trials=None, kind='non_repeating')
    speaker_1 = list(20, 26)
    speaker_1 = slab.Trialsequence(conditions=speaker_1, n_reps=60, trials=None, kind='non_repeating')
    if speaker_1 == 20:
        channel = 22, 24, 26
        probe.play()
        probe.wait_to_finish_playing()
        interval.play()
    else:
        channels = 20, 22, 24
        probe.play()
        probe.wait_to_finish_playing()
        interval.play()

    # 5% of trials, tone after the inter-stimulus interval and localization
    x = [randint(0, 239) for p in range(0, 239)]
    if x <= 0.05:
        probe.play()
    with slab.key() as key:  # wait for a key press
      response = key.getch()


# loop over trials
    data_dir.mkdir(parents=True, exist_ok=True)  # create subject data directory if it doesnt exist
    file_name = 'localization_' + subject_id + '_' + condition + date.strftime('_%d.%m')
    counter = 1
    while Path.exists(data_dir / file_name):
        file_name = 'localization_' + subject_id + '_' + condition + date.strftime('_%d.%m') + '_' + str(counter)
        counter += 1

