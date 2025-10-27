#! /usr/bin/env python
# Time-stamp: <2024-14-04 m.utrosa@bcbl.eu>

# LIBRARIES and PACKAGES
from expyriment import design, control, stimuli, io, misc
import detection_modular as dm

# CREATE EXPERIMENT
exp = expyriment.design.Experiment(name = "odd_timing_MRI")

# INITIALIZE EXPERIMENT
control.initialize(exp)
control.set_develop_mode(on=True) # When developping == True, when testing == False.

# CREATE EXPYRIMENT STIMULI
keyboard = io.Keyboard()
canvas = stimuli.Canvas(size=params["CANVAS_SIZE"], colour=params["BLACK"])
fixation_cross = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"],line_width=params["FIXATION_CROSS_WIDTH"], colour=params["WHITE"])

deviations = dm.Devil(start=-300, end=300, step=10)
deviations.add_deviation([5, -5, 15, -15])

# PRELOAD EXPYRIMENT STIMULI 

# START EXPERIMENT
control.start()

## BLOCKS
exp.design.Block

## TRIALS
exp.design.Trial

control.end()