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
subject_dir = data_dir / 'experiment' / 'familiarization' / subject_id / condition

repetitions = 6  # number of repetitions per speaker
target_speakers = (19, 21, 23, 25, 27)

def familiarization_test(target_speakers, repetitions, subject_dir):
    global sequence, tone, probes, adapters
    proc_list = [['RX81', 'RX8', data_dir / 'rcx' / 'play_adapter_probe.rcx'],
                 ['RX82', 'RX8', data_dir / 'rcx' / 'play_adapter_probe.rcx'],
                 ['RP2', 'RP2', data_dir / 'rcx' / 'button.rcx']]
    freefield.initialize('dome', device=proc_list, sensor_tracking=True)
    # todo create a good calibration file


    # --- generate sounds ---- #
    # adapter
    # generate adapter
    adapter_duration = 1.0
    adapter_n_samples = int(adapter_duration*samplerate)
    adapters = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=adapter_duration), n=20)
    freefield.write(tag='n_adapter', value=adapter_n_samples, processors='RX82') # write the samplesize of the adapter to the processor
    # freefield.write(tag='data_adapter', value=adapter.data, processors='RX82') # write the adapter to the processor
    # set adapter speakers
    adapter_speaker_ids = [0, 42]
    adapter_speakers = freefield.pick_speakers(adapter_speaker_ids)
    freefield.write(tag='adapter_ch_1', value=adapter_speakers[0].analog_channel, processors='RX82')
    freefield.write(tag='adapter_ch_2', value=adapter_speakers[1].analog_channel, processors='RX82')

    # probe
    probe_duration = 0.1
    probe_n_samples = int(numpy.round(probe_duration * samplerate))
    probes = slab.Precomputed(lambda: slab.Sound.pinknoise(duration=probe_duration), n=20)
    # set probe buffer parameters
    freefield.write(tag='n_probe', value=probe_n_samples, processors='RX81')
    # probe-adapter-cross-fading
    probe_onset = adapter_n_samples - int(0.005 * samplerate)  # delay of probe vs adapter
    freefield.write(tag='probe_onset', value=probe_onset, processors='RX81')

    # signal tone
    tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    freefield.write(tag='n_tone', value=tone.n_samples, processors='RX81')
    freefield.write(tag='data_tone', value=tone.data, processors='RX81')

    input("Press Enter to start.")

    # create subject folder
    subject_dir.mkdir(parents=True, exist_ok=True)  # create subject data directory if it doesnt exist
    # generate random sequence of target speakers
    sequence = slab.Trialsequence(conditions=target_speakers, n_reps=repetitions, kind='non_repeating')


    for target_speaker_id in sequence:
        sequence.add_response(play_trial(target_speaker_id))
        sequence.save_pickle(subject_dir / str('familiarization' + date.strftime('_%d.%m')), clobber=True)

    # save trialsequence
    return

def play_trial(target_speaker_id):
    # generate and write probe
    probe = random.choice(probes)
    adapter = random.choice(adapters)

    # write probe and adapter
    freefield.write(tag='data_probe', value=probe.data, processors='RX81')
    freefield.write(tag='data_adapter', value=adapter.data, processors='RX82')

    # set probe speaker
    [probe_speaker] = freefield.pick_speakers(target_speaker_id)
    freefield.write(tag='probe_ch', value=probe_speaker.analog_channel, processors=probe_speaker.analog_proc)

    # -- get head pose offset --- #
    freefield.calibrate_sensor()
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
    return numpy.array((pose, (probe_speaker.azimuth, probe_speaker.elevation)))



if __name__ == "__main__":
    familiarization_test(target_speakers, repetitions, subject_dir)







    #
    # # freefield.load_equalization(Path.cwd() / 'data' / 'calibration' / 'calibration_dome_23.05.pkl')
    #
    # # generate stimulus
    # bell = slab.Sound.read(Path.cwd() / 'data' / 'sounds' / 'bell.wav')
    # bell.level = 75
    # tone = slab.Sound.tone(frequency=1000, duration=0.25, level=70)
    #
    #
    # interval = slab.Sound.silence(duration=0.35)
    #
    # stimulus = probe.ramp(duration=0.05, when='both', level=70)
    # for channels in seq:
    #     # write channel to rcx
    #     stimulus.level = probe
    #     stimulus.play()
    # with slab.key() as key:
    #     response = key.getch()
    #     # get head position
    # seq.add_response(response)
    # # first 15 stimuli are accompanied by a visual cue
    #
    # stimulus.wait_to_finish_playing()
    # response = 0
    # while not response:
    #     pose = freefield.get_head_pose(method='sensor')
    #     if all(pose):
    #         print('head pose: azimuth: %.1f, elevation: %.1f' % (pose[0], pose[1]), end="\r", flush=True)
    #     else:
    #         print('no head pose detected', end="\r", flush=True)
    #     response = freefield.read('response', processor='RP2')
    # if all(pose):
    #     print('Response| azimuth: %.1f, elevation: %.1f' % (pose[0], pose[1]))
    # freefield.set_signal_and_speaker(signal=tone, speaker=23)
    # freefield.play()
    # freefield.wait_to_finish_playing()
    # return numpy.array((pose, probe))
#
# def play_trial(speaker_id):
#     probe = slab.Sound.pinknoise(duration=0.1)