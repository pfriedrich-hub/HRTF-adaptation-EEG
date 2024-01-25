import random
import freefield
import slab
import numpy
import time
import datetime
date = datetime.datetime.now()
# import matplotlib
# matplotlib.use('GTK3Agg')
from matplotlib import pyplot as plt
from pathlib import Path

samplerate = 48828
slab.set_default_samplerate(samplerate)
data_dir = Path.cwd() / 'data'

# initial test
subject_id = '1'
condition = 'Ears Free'
subject_dir = data_dir / 'experiment' / 'EEG' / subject_id / condition

repetitions = 60  # number of repetitions per speaker
n_blocks = 1
target_speakers = (20, 22, 24, 26)
probe_level = 85
adapter_level = 85

def eeg_test(target_speakers, repetitions, subject_dir):
    global sequence, tone, probes, adapters, response_trials
    proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RX82', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RP2', 'RP2', data_dir / 'rcx' / 'play_adapter.rcx']]
    freefield.initialize('dome', device=proc_list, sensor_tracking=True)
    # todo create a good calibration file

    # --- generate sounds ---- #
    # adapter
    # generate adapter
    adapter_duration = 1.0
    adapter_n_samples = int(adapter_duration*samplerate)
    adapters = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration, level=adapter_level), n=20)
    freefield.write(tag='n_adapter', value=adapter_n_samples, processors='RP2')  # write the samplesize of the adapter to the processor

    # probe
    probe_duration = 0.1
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    probes = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=probe_duration, level=probe_level), n=20)
    # set probe buffer parameters
    freefield.write(tag='n_probe', value=probe_n_samples, processors='RX81')
    # probe-adapter-cross-fading
    probe_onset = adapter_n_samples - int(0.005 * samplerate)  # delay of probe vs adapter
    freefield.write(tag='probe_onset', value=probe_onset, processors='RX81')

    # signal tone
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    freefield.write(tag='n_tone', value=tone.n_samples, processors='RX81')
    freefield.write(tag='data_tone', value=tone.data, processors='RX81')
    freefield.write(tag='ch_tone', value=23, processors='RX81')

    input("Press Enter to start.")


    # create subject folder
    subject_dir.mkdir(parents=True, exist_ok=True)  # create subject data directory if it doesnt exist

    for block in range(n_blocks):
        freefield.write('bitmask', value=8, processors='RX81')  # turn on LED

        # get trial indices for response trials
        n_trials = int(repetitions * len(target_speakers))
        n_response_trials = int(n_trials * 0.05)
        response_trials = []
        for i in range(n_response_trials):
            temp = [0] * int(n_trials / n_response_trials)
            temp[numpy.random.randint(2, n_response_trials-2)] = 1
            response_trials.extend(temp)
        response_trials = numpy.where(numpy.asarray(response_trials) == 1)[0]
        # generate random sequence of target speakers
        sequence = slab.Trialsequence(conditions=target_speakers, n_reps=repetitions, kind='non_repeating')

        # play trial sequence
        for target_speaker_id in sequence:
            sequence.add_response(play_trial(target_speaker_id))  # play trial
            sequence.save_pickle(subject_dir / str('familiarization' + date.strftime('_%d.%m')), clobber=True)    # save trialsequence
        freefield.write('bitmask', value=0, processors='RX81')  # turn off LED
        input("Press Enter to start the next Block.")
    return

def play_trial(target_speaker_id):
    # generate and write probe
    probe = random.choice(probes)
    adapter = random.choice(adapters)
    # get probe speaker
    [probe_speaker] = freefield.pick_speakers(target_speaker_id)
    # write probe and adapter data
    freefield.write(tag='data_probe', value=probe.data, processors=probe_speaker.analog_proc)
    freefield.write(tag='data_adapter', value=adapter.data, processors='RP2')
    # set probe channel
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)
    # set eeg marker to current target speaker ID
    freefield.write('eeg marker', value=target_speaker_id, processors='RX82')

    # play adaptor and probe
    freefield.play()
    time.sleep(0.9 - 0.195)  # account for the time it needs to write data to the processor
    pose = (None, None)
    if sequence.this_n in response_trials.tolist():
        freefield.play('zBusB')  # play tone  #todo tone doesnt play
        # -- get head pose offset --- #
        freefield.calibrate_sensor(led_feedback=True, button_control=False)
        # get headpose with a button response
        time.sleep(0.25)
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
        freefield.play('zBusB')
        freefield.write('bitmask', value=8, processors='RX81')  # turn on LED
        time.sleep(0.25)  # wait until the tone has played
        freefield.wait_for_button()
    return numpy.array((pose, (probe_speaker.azimuth, probe_speaker.elevation)))


if __name__ == "__main__":
    eeg_test(target_speakers, repetitions, subject_dir)

