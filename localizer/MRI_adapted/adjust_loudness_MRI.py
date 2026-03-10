#! /usr/bin/env python
# Time-stamp: <2025-09-10 m.utrosa@bcbl.eu>

# 1. PREPARATION ----------------------------------------------------------------------------------
import random, glob, os
from expyriment import design, control, stimuli, io, misc
control.set_develop_mode(on = False) # While developping True, while testing False.

params = {
	# Local setup
	"AUDIO_DIRECTORY" : "C:/Users/Experimental User/Desktop/SUBCORT_HIGHRES/",
	"AUDIOFILE_REGEX" : "**/*.wav",
	
	# Audio
	"SOUND_DURATION"   : 1000, # milliseconds
	"SOUNDS_PER_TRIAL" : 2,

	# Visual
	"CANVAS_SIZE" : (1024, 768), # Monitor resolution.

	"FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,

	"BLACK" : (0, 0, 0),	   # screen background
	"WHITE" : (255, 255, 255), # fixation cross
}

# 1. PREPARATION ----------------------------------------------------------------------------------
# Import audio files
wav_filepaths = glob.glob(f'{params["AUDIO_DIRECTORY"]}/{params["AUDIOFILE_REGEX"]}')
sounds_all = ["stimuli" + file_1.split("stimuli", 1)[1] for file_1 in wav_filepaths if "s3" in file_1]
random.shuffle(sounds_all)

# 3. SET UP LOGGING & INITIALIZE THE EXPERIMENT ---------------------------------------------------
exp = design.Experiment(name = "loudness")
control.initialize(exp)

# 4. CREATE & PRELOAD THE STIMULI -----------------------------------------------------------------
# Creating
keyboard = io.Keyboard()
sounds = {filename: stimuli.Audio(filename) for filename in sounds_all}
canvas = stimuli.Canvas(size=params["CANVAS_SIZE"], colour=params["BLACK"])
fixation_cross = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["WHITE"])
# Preloading
fixation_cross.preload(); fixation_cross.plot(canvas); canvas.preload();
for s in sounds.values():
	s.preload()

# 5. RUN THE EXPERIMENT ---------------------------------------------------------------------------
# Start the loudness adjustment.
control.start(skip_ready_screen = True) # Start the experiment without the ready screen and wait for trigger from the MRI.
canvas.present()

while True:
	key, rt = keyboard.wait(keys = [misc.constants.K_g, misc.constants.K_e])

	# Play sounds when 'g' is pressed (GO).
	if key == 103: # ASCII code
		for i in range(params['SOUNDS_PER_TRIAL']):
			i_random = random.choice(list(sounds.items()))
			i_sound = i_random[1]
			i_sound.play()
			exp.clock.wait(params["SOUND_DURATION"])

	# End experiment when 'e' is pressed (END).
	if key == 101: # ASCII code
		break

# Finishing
control.end(goodbye_text = "Great, thanks! Take a short break now.")
