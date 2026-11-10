#! /usr/bin/env python
# Time-stamp: <10-11-2026, m.utrosa@bcbl.eu>
'''
Configuration of variables for creation of main task stimuli and presentation of the task.
Requires Expyriment version 1.0.0
'''
import numpy as np
from pathlib import Path
from expyriment import design, control, stimuli, misc, io

# 00. Directories -----------------------------------------------------------------------
n_blocks = 5
homePath = Path("/home/mutrosa/Documents/projects/")
projPath = homePath / "auditory_paradigms" / "flash_detection"
outPath  = projPath / "tests"
outPath.mkdir(exist_ok=True, parents=True)
write_wav = True

# 01. PARAMETERS ------------------------------------------------------------------------
params = {
    
    # Overall structure of the experimental session ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "DEVELOP_MODE" : True,
    "NO_MRI_RUNS" : 5,       # How many functional runs are in one session?
    "RUN_DURATION_MIN" : 12, # Duration of the functional run in minutes

    # Timing and pitch deviant tones ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "TIM_DEVS"    : [4, 8, 13, 19, 27, 36, 48, 63, 80, 100, 125], # msec
    "PIT_DEVS"    : [4, 8, 13, 19, 27, 36, 48, 63, 80, 100, 125], # Hz
    "TIM_DEV_REP" : 2, # How many times does a deviation repeat per run?
    "PIT_DEV_REP" : 2, # How many times does a deviation repeat per run?
    "TIME_BETWEEN_DEVS_MIN" : 4500,  # ms - Friston et al. (1999)
    "TIME_BETWEEN_DEVS_MAX" : 6500,  # ms - Friston et al. (1999)
    "NO_DEV_PERIOD_TIME" : 20, # sec - duration of the "silent" period
                               # Corresponds to a longer period of standard tones
    "NO_DEV_PERIOD_REP"  : 4,  # How many "silent" periods occur in one run?
                               # Excluding the "silent" periods at the start & end.

    # Standard tones ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "FREQ_MIN" : 200,  # Hz
    "FREQ_MAX" : 500,  # Hz
    "MIN_STD_END" : 4, # Min. no. of standards at the end of the sequence (inclusive)
    "MAX_STD_END" : 6, # Max. no. of standards at the end of the sequence (insclusive)
    "ISI_MIN"  : 500,  # Min. duration of ISI in ms
    "ISI_MAX"  : 500,  # Max. duration of ISI in ms
    "ISI_STEP" : 1,    # Step size of the ISI range

    # Flash events (distractor task) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "FLASH_POSITION" : (0, 0), # (0,0) is the center of the screen
    "FLASH_RADIUS"   : 45,     # Size of the disk
    "FLASH_PROB"     : 0.15,   # Probability of the flash
    "FLASH_REP_MAX"  : 3,      # How many times max can the disk flash?
                               # If 4, it means there could be 1, 2, 3 or 4
                               # flashes per tone period (tone duration + 
                               # ISI. That's the max because we only
                               # have 4 buttons in the MRI response box.
    "FLASH_ISI_MIN"  : 55,     # Longer than FLASH_DURATION
    "FLASH_ISI_MAX"  : 65,     # Small enough so that flashes fit within tone ISI
    "FLASH_DURATION" : 50,     # How long is the stimulus that flashes presented for?

    ## Responses
    # In the MRI, the rainbow response pad is 1234, while the white one is abcd.
    "DETECTION_SYMBOL"   : [misc.constants.K_1, misc.constants.K_2, misc.constants.K_3, misc.constants.K_4],
    "DETECTION_ASCII"    : ['49', '50', '51', '52'],
    "MAX_RESPONSE_TIME" : 2000, # ms; max time for participant's response
    "MAX_FEEDBACK_TIME" : 1000, # ms; duration of color change for trial-by-trial response feedback
    
    # General audio settings ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ## Stimuli for main task
    "TONE_LOUDNESS"   : 85,     # dB SPL
    "TONE_DURATION"   : 50,     # msec
    "NUM_HARMONICS"   : 10,     # Number of harmonics
    "HARMONIC_FACTOR" : 0.8,    # Harmonic amplitude decay factor
    "MAX_AMPLITUDE"   : 1.14,   # Defined through a simulation
    "SAMPLE_RATE"     : 48000,  # Hz
    "TAU"             : 5,      # Ramping window in msec
    
    ## Sound stimuli in localizer
    "SOUND_STRATA"     : 84,   # the total amount of available sounds
    "SOUND_DURATION"   : 1000, # msec
    "SOUND_REP_PROB"   : .05,  # low enough to be stimulating/challenging

    # General visual settings ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "CANVAS_SIZE"             : (1920,  1200), # Linux Mint monitor resolution.
    "FIXATION_CROSS_SIZE"     : (40, 40),
    "FIXATION_CROSS_POSITION" : (0, 0),
    "FIXATION_CROSS_WIDTH"    : 5,
    "HEADING_SIZE"            : 30, 
    "TEXT_SIZE"               : 25,

    ## Colors
    "BLACK"   : (0, 0, 0),       # screen background
    "WHITE"   : (255, 255, 255), # fixation cross
    "CORRECT" : (70, 255, 255),  # cyan; color contrast on black is super (17.01)
    "WRONG"   : (255, 234, 0),   # yellow; color contrast on black is super (17.02)
    "GRAY"    : (158, 88, 238),  # gray; color contrast on black is ?? (??)
    
    # Text ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "INTRO_HEADING"   : f"Welcome to the ",
    "INTRO_TEXT_TASK" : f"When the experiment starts, you will see a white cross in the center of the screen.\n"
                        "Please look at the cross for the entire duration of the task.\n\n"
                        "Your task is to count how many times the cross twitches.\n "
                        "There may be 0, 1, 2 or 3 twitches.\n\n"
                        "If you counted well and were fast enough, the cross will change color to bright blue.\n"
                        "If you made a mistake or were too slow, the cross will change color to bright yellow.\n\n"
                        "You will also hear a series of sounds. These are unrelated to your task.\n"
                        "Sometimes, there will be no sound for a while. "
                        "During this time, please just relax and stay still.\n\n"
                        f"We will repeat this task {n_blocks} times.\n"
                        "You will have short breaks in between.\n\n\n"
                        "It is very very important that you DO NOT MOVE your arms, legs, or head until the break.\n\n"
                        "Thank you and good luck!\n\n\n"
                        "Whenever you are ready, press any button.",
    "INTRO_TEXT_LOC"  :  f"When the experiment starts, you will see a white cross in the center of the screen.\n"
                        "Please look at the cross for the entire duration of the task.\n\n"
                        "You will hear a series of short sounds (animals, speech, or tools).\n"
                        "Sometimes, the same sound will play twice in a row.\n"
                        "When you hear a sound repeat, press any button as fast as you can.\n\n"
                        "If you you were correct and fast enough, the cross will change color to cyan.\n"
                        "If you made a mistake or were too slow, the cross will change color to yellow.\n\n"
                        "Each sound series will be separated by a longer silent period.\n"
                        "During these periods, please just relax and stay still.\n\n"
                        "It is very important that you do NOT move your arms, legs, or head until the break.\n\n"
                        "Thank you so much and good luck!\n\n\n"
                        "Whenever you are ready to start, press any button.",

    "REST_HEADING" : "BREAK TIME",
    "REST_TEXT"    : "\n\nPlease take a moment to rest and move your body as needed.\n\n"
                     "Whenever you are ready to continue, press any button.",
    
    "MRI_HEADING"  : "SCANNER CALIBRATION",
    "MRI_TEXT"     : "Please do not move. Stay still for a few moments.\n\n"
                     "Do not move your body or head until the break.\n\n"
                     "Thank you!",

    "TASK_END_HEADING" : "You have reached the end of the ", 
    "TASK_END_TEXT"    : "Thank you so much!\n\n",

    "END_HEADING"      : "The End of the Experiment", 
    "END_TEXT"         : "Thank you so much for your participation!\n\n",
    "READING_TIME": 30 # ms; ensures that the participant reads the instructions
                       # at the start & end of the experiment
}

# 02. FUNCTIONS -------------------------------------------------------------------------
def feedback_flash(current_event, response, good, bad):
    '''
    Determines the response category for a given response in the flash counting task.
    Gives feedback by changing the color of the fixation cross.
    
    Parameters:
    - current_event: The number of flashes in the current event.
    - response: The identity of the key pressed in ASCII code.
    - good: A class implementing fixation cross for correct responses.
    - bad: A class implementing fixation cross for wrong responses.

    Returns:
    - perfo_code: The response category (str).
    - trial_performance: Dictionary tracking performance across trials (dict).
    '''
    perfo_code = None
    trial_performance = {"CORRECT": 0, "INCORRECT": 0}
    
    # Correct for MRI buttons
    if response is not None:
        response_str = chr(response)
    else:
        response_str = "None"

    # Ensure that you are comparing variables of the same type (str)
    current_event_str = str((int(current_event)))

    # ----- Correct count -----
    if current_event_str == response_str:
        good.present()
        trial_performance["CORRECT"] += 1
        perfo_code = "CORRECT"
    
    # ----- Incorrect count ----- 
    else:
        bad.present()
        trial_performance["INCORRECT"] += 1
        perfo_code = "INCORRECT"

    return perfo_code, trial_performance

def twitch(stimulus, duration, isi, screen, clock, keyboard):
    '''
    Presents a flash, which is presented for the specified time and 
    then removed from the canvas screen. The empty screen is presented 
    for the same waiting time before another flash is drawn on the canvas.
    '''
    # Check for quit key
    keyboard.check(keys=[misc.constants.K_y])
    
    # Present the stimulus for the specified duration
    stimulus.present()
    clock.wait(duration)

    # Present the screen (without the stimulus)
    screen.present()

    # Wait until presenting the stimulus again
    clock.wait(isi)