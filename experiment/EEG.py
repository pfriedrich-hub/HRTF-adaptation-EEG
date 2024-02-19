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
subject_id = 'Fee'
condition = 'Ear molds'
subject_dir = data_dir / 'experiment' / 'EEG' / subject_id / condition

repetitions = 60  # number of repetitions per speaker
n_blocks = 6
target_speakers = (20, 22, 24, 26)
probe_level = 75
adapter_levels = (44, 49)  # calibrated adapter levels, left first
isi = 1.0  # inter stim interval in seconds

def eeg_test(target_speakers, repetitions, subject_dir):
    global sequence, tone, probes, adapters_l, adapters_r, response_trials
    proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RX82', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RP2', 'RP2', data_dir / 'rcx' / 'play_rec_adapter.rcx']]
    freefield.initialize('dome', device=proc_list, sensor_tracking=True)
    # todo create a good calibration file
    freefield.set_logger('error')
    # --- generate sounds ---- #
    # adapter
    # generate adapter
    adapter_duration = 1.0
    adapter_n_samples = int(adapter_duration*samplerate)
    adapters_l = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration, level=adapter_levels[0]), n=20)
    adapters_r = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration, level=adapter_levels[1]), n=20)
    # todo ramp probe and adapter
    freefield.write(tag='n_adapter', value=adapter_n_samples, processors='RP2')  # write the samplesize of the adapter to the processor
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')

    # probe
    probe_duration = 0.1
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    probes = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=probe_duration, level=probe_level), n=20)
    # set probe buffer parameters
    freefield.write(tag='n_probe', value=probe_n_samples, processors='RX81')

    # probe-adapter-cross-fading
    adapter_ramp_onset = adapter_n_samples - int(0.005 * samplerate)
    freefield.write(tag='adapter_ramp_onset', value=adapter_ramp_onset, processors='RP2')
    # delay of probe vs adapter, plus time the sound needs to reach the eardrum
    sound_travel_delay = int(1.4 / 344 * samplerate)
    dac_delay_RX8 = 24
    dac_delay_RP2 = 30
    dac_delay = dac_delay_RX8 - dac_delay_RP2
    probe_ramp_onset = adapter_ramp_onset - sound_travel_delay - dac_delay
    freefield.write(tag='probe_onset', value=probe_ramp_onset, processors='RX81')

    # signal tone
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    freefield.write(tag='n_tone', value=tone.n_samples, processors='RX81')
    freefield.write(tag='data_tone', value=tone.data, processors='RX81')
    freefield.write(tag='ch_tone', value=23, processors='RX81')

    input("Press Enter to start.")

    # create subject folder
    subject_dir.mkdir(parents=True, exist_ok=True)  # create subject RCX_files directory if it doesnt exist

    for block in range(n_blocks):
        # freefield.write('bitmask', value=8, processors='RX81')  # turn on LED
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
            time.sleep(isi - 0.195)  # account for the time it needs to write RCX_files to the processor (0.195 seconds)
            sequence.save_pickle(subject_dir / str(('familiarization' + '_block_%i' + date.strftime('_%d.%m')) % block),
                                 clobber=True)    # save trialsequence
        # freefield.write('bitmask', value=0, processors='RX81')  # turn off LED
        input("Press Enter to start the next Block.")
    return

def play_trial(target_speaker_id):
    # generate and write probe
    probe = random.choice(probes)
    adapter_l = random.choice(adapters_l)
    adapter_r = random.choice(adapters_r)
    # get probe speaker
    [probe_speaker] = freefield.pick_speakers(target_speaker_id)

    # write probe and adapter RCX_files
    freefield.write(tag='data_probe', value=probe.data, processors=probe_speaker.analog_proc)
    freefield.write(tag='data_adapter_l', value=adapter_l.data, processors='RP2')
    freefield.write(tag='data_adapter_r', value=adapter_r.data, processors='RP2')

    # set probe channel
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)

    # set eeg marker to current target speaker ID
    freefield.write('eeg marker', value=target_speaker_id, processors='RX82')

    # play adaptor and probe
    freefield.play()
    time.sleep(1.1)  # wait for the stimuli to finish playing
    pose = (None, None)
    if sequence.this_n in response_trials.tolist():
        freefield.set_logger('error')
        freefield.play('zBusB')  # play tone
        # -- get head pose offset --- #
        freefield.calibrate_sensor(led_feedback=False, button_control=False)
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
        # freefield.write('bitmask', value=8, processors='RX81')  # turn on LED
        time.sleep(0.25)  # wait until the tone has played
        freefield.wait_for_button()
        freefield.set_logger('error')
    print(sequence.this_n)
    return numpy.array((pose, (probe_speaker.azimuth, probe_speaker.elevation)))

if __name__ == "__main__":
    eeg_test(target_speakers, repetitions, subject_dir)
    freefield.halt()



""" test localization file

import slab
from pathlib import Path
from analysis.plotting.localization_plot import localization_accuracy

file_name = 'familiarization_block_0_31.01'

for path in Path.cwd().glob("**/"+str(file_name)):
    file_path = path
sequence = slab.Trialsequence(conditions=4, n_reps=60, kind='non_repeating')
sequence.load_pickle(file_path)

# plot
from matplotlib import pyplot as plt
fig, axis = plt.subplots(1, 1)
elevation_gain, ele_rmse, ele_var, az_rmse, az_var = localization_accuracy(sequence, show=True, plot_dim=2,
 binned=True, axis=axis)
axis.set_xlabel('Response Azimuth (degrees)')
axis.set_ylabel('Response Elevation (degrees)')
fig.suptitle(file_name)

"""