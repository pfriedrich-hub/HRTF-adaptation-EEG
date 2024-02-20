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
subject_id = 'Fee'
condition = 'Ears Free'
subject_dir = data_dir / 'experiment' / 'familiarization' / subject_id / condition


repetitions = 6  # number of repetitions per speaker
target_speakers = (19, 21, 23, 25, 27)
adapter_levels = (44, 49)  # calibrated adapter levels, left first

def familiarization_test(target_speakers, repetitions, subject_dir):
    global sequence, tone, probes, adapters_l, adapters_r
    proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RX82', 'RX8', data_dir / 'rcx' / 'play_probe.rcx'],
                 ['RP2', 'RP2', data_dir / 'rcx' / 'play_rec_adapter.rcx']]
    freefield.initialize('dome', device=proc_list, sensor_tracking=True)
    # todo create a good calibration file

    # --- generate sounds ---- #
    # adapter
    # generate adapter
    adapter_duration = 1.0
    adapter_n_samples = int(adapter_duration*samplerate)
    adapters_l = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration, level=adapter_levels[0]), n=20)
    adapters_r = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration, level=adapter_levels[1]), n=20)
    freefield.write(tag='n_adapter', value=adapter_n_samples, processors='RP2') # write the samplesize of the adapter to the processor
    freefield.write(tag='adapter_ch_1', value=1, processors='RP2')
    freefield.write(tag='adapter_ch_2', value=2, processors='RP2')

    # probe
    probe_duration = 0.1
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    probes = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=probe_duration), n=20)
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

    input("Press Enter to start.")

    # create subject folder
    subject_dir.mkdir(parents=True, exist_ok=True)  # create subject RCX_files directory if it doesnt exist
    # generate random sequence of target speakers
    sequence = slab.Trialsequence(conditions=target_speakers, n_reps=repetitions, kind='non_repeating')

    for target_speaker_id in sequence:
        sequence.add_response(play_trial(target_speaker_id))
        sequence.save_pickle(subject_dir / str('familiarization' + date.strftime('_%d.%m')), clobber=True)
    freefield.halt()  # disconnect sensor and processors
    return

def play_trial(target_speaker_id):
    # generate and write probe
    probe = random.choice(probes)
    adapter_l = random.choice(adapters_l)
    adapter_r = random.choice(adapters_r)

    # write probe and adapter
    freefield.write(tag='data_probe', value=probe.data, processors='RX81')
    freefield.write(tag='data_adapter_l', value=adapter_l.data, processors='RP2')
    freefield.write(tag='data_adapter_r', value=adapter_r.data, processors='RP2')

    # set probe speaker
    [probe_speaker] = freefield.pick_speakers(target_speaker_id)
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)

    # -- get head pose offset --- #
    freefield.calibrate_sensor(led_feedback=True, button_control=True)
    # play adaptor and probe
    freefield.play()
    # activate led
    if sequence.this_n < 15: # make sure the light is only activated for the first 15 trials
        while not freefield.read('playback', 'RX81') == 1:  # wait until probe onset
            time.sleep(0.01)
        freefield.write('bitmask', value=probe_speaker.digital_channel, processors='RX81')
        # freefield.wait_to_finish_playing()
        time.sleep(.5)
        freefield.write('bitmask', value=0, processors='RX81')
        # todo make sure the light is on for an adequate amount of time
    # get headpose with a button response
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
    time.sleep(0.25)  # wait until the tone has played
    print(f'{sequence.this_n}')
    return numpy.array((pose, (probe_speaker.azimuth, probe_speaker.elevation)))



if __name__ == "__main__":
    familiarization_test(target_speakers, repetitions, subject_dir)
