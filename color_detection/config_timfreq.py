from expyriment import design, control, stimuli, misc, io

# Parameters for the color detection experiment
n_blocks = 4

# 01. PARAMETERS ------------------------------------------------------------------------
params = {

    # Developer mode
    "DEVELOP_MODE" : True,

    # Directories
    "PROJECT_ROOT" : "/home/mutrosa/Documents/projects/auditory_paradigms/color_detection",
    
    # Experiment structure
    "WAIT_TIME" : 3000, # msec (ensuring reading at the start & end of the experiment)
    
    # Visual
    "CANVAS_SIZE"             : (1920,  1200), # Linux Mint monitor resolution.
    "FIXATION_CROSS_SIZE"     : (40, 40),
    "FIXATION_CROSS_POSITION" : (0, 0),
    "FIXATION_CROSS_WIDTH"    : 5,
    "HEADING_SIZE"            : 30, 
    "TEXT_SIZE"               : 25, 
    
    "FLASH_RADIUS" : 45,
    "FLASH_POSITION" : (0, 0),
    "FLASH_ISI" : 57,

    # Colors in RGB
    "BLACK"   : (0, 0, 0),       # screen background
    "WHITE"   : (255, 255, 255), # fixation cross
    "CORRECT" : (70, 255, 255),  # cyan; color contrast on black is super (17.01)
    "WRONG"   : (255, 234, 0),   # yellow; color contrast on black is super (17.02)
    "GRAY"    : (158, 88, 238), # gray; color contrast on black is ?? (??)
    
    # Sound stimuli in localizer
    "SOUND_STRATA"     : 84,   # the total amount of available sounds
    "SOUND_DURATION"   : 1000, # msec
    "SOUND_REP_PROB"   : .05,  # low enough to be stimulating/challenging

    # In the MRI, the rainbow response pad is 1234, while the white one is abcd.
    "DETECTION_SYMBOL"   : [misc.constants.K_1, misc.constants.K_2, misc.constants.K_3, misc.constants.K_4],
    "DETECTION_ASCII"    : ['49', '50', '51', '52'],

    # Text (for instructions and goodbye message)
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
}

# 02. FUNCTIONS -------------------------------------------------------------------------
def twitch(flash, flash_isi, canvas, cross, clock, keyboard):
    '''
    Presents a flash, which is presented for the specified time and 
    then removed from the canvas screen. The empty screen is presented 
    for the same waiting time before another flash is drawn on the canvas.
    '''

    # Check if quit key is pressed during flashing
    keyboard.check(keys=[misc.constants.K_y])
    
    # Present the circle (flash)
    flash.plot(canvas)
    canvas.present()
    clock.wait(flash_isi)

    # Erase it from screen
    canvas.clear_surface()

    # Present the fixation cross
    cross.plot(canvas)
    canvas.present()

    # Wait until presenting the circle again
    clock.wait(flash_isi)