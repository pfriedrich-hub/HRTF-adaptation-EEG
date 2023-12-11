import random
import math
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
from matplotlib import pyplot as plt
from pathlib import Path
from analysis.localization_analysis import localization_accuracy
fs = 48828
slab.set_default_samplerate(fs)

# EEG experiment (experiment 2)
subject_id = '1'
condition = 'Ears Free'
data_dir = Path.cwd() / 'HRTF-adaptation-EEG' / 'Experiments' / 'EEG_without_molds' / subject_id / condition

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

    #5% of trials, tone after the inter-stimulus interval and localization
    if math.random() <= 0.05:
        probe.play()
    if seq.this_n > 0:

    with slab.key() as key:  # wait for a key press
      response = key.getch()


# loop over trials
    data_dir.mkdir(parents=True, exist_ok=True)  # create subject data directory if it doesnt exist
    file_name = 'localization_' + subject_id + '_' + condition + date.strftime('_%d.%m')
    counter = 1
    while Path.exists(data_dir / file_name):
        file_name = 'localization_' + subject_id + '_' + condition + date.strftime('_%d.%m') + '_' + str(counter)
        counter += 1
    played_bell = False
    print('Starting...')
    for index in trial_sequence:
        progress = int(trial_sequence.this_n / trial_sequence.n_trials * 100)
        if progress == 50 and played_bell is False:
            freefield.set_signal_and_speaker(signal=bell, speaker=23)
            freefield.play()
            freefield.wait_to_finish_playing()
            played_bell = True
        trial_sequence.add_response(play_trial(sequence[index], progress))
        trial_sequence.save_pickle(data_dir / file_name, clobber=True)
    # freefield.halt()
    print('localization ole_test completed!')
    return trial_sequence
