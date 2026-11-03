#! /usr/bin/env python
# Time-stamp: <02-11-2026 m.utrosa@bcbl.eu>
# 00A. IMPORT
import sys
import random
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product

# 00B. PARAMETERS
par = {
	# a. Timing deviants
	"TIM_DEVS"    : [4, 8, 13, 19, 27, 36, 48, 63, 80, 100, 125], # Absolute timing deviants in msec
	"TIM_DEV_REP" : 4, # How many times should each deviation repeat in one MRI run?

	# b. Pitch deviants
	"PIT_DEVS"    : [4, 8, 13, 19, 27, 36, 48, 63, 80, 100, 125], # Absolute pitch deviants in Hz
	"PIT_DEV_REP" : 4,	# How many times should each deviation repeat in one MRI run?

	# c. Overall structure of the experimental session
	"NO_MRI_RUNS" : 4, # How many functional scans are in one experimental session?
	"RUN_DURATION_MIN" : 10, # What is the duration of the functional run in minutes?
	"TIME_BETWEEN_DEVS_MIN" : 5000, # ms
	"TIME_BETWEEN_DEVS_MAX" : 8000, # ms
	"FREQ_MIN" : 200, # Hz
	"FREQ_MAX" : 500, # Hz
	"ISI_MIN"  : 500, # Min. duration of ISI in ms
	"ISI_MAX"  : 600, # Max. duration of ISI in ms
	"ISI_STEP" : 1,   # Step size of the ISI range (population) TODO: this may be obsolete for MRI (not for beh)
	"TONE_DURATION" : 50,  # Duration of a single tone in ms
}

# 01. GENERATE INDEPENDENT VARIABLES
# Create negative values for deviations.
TIM_DEV_pos = np.array(par["TIM_DEVS"])
TIM_DEV_neg = -TIM_DEV_pos
PIT_DEV_pos = np.array(par["PIT_DEVS"])
PIT_DEV_neg = -PIT_DEV_pos

# Combine positive and negative values into a sorted list.
TIM_DEV_arr = np.concatenate([TIM_DEV_pos, TIM_DEV_neg])
TIM_DEV     = np.sort(TIM_DEV_arr).tolist()
PIT_DEV_arr = np.concatenate([PIT_DEV_pos, PIT_DEV_neg])
PIT_DEV     = np.sort(PIT_DEV_arr).tolist()

# Define possible "types" of deviations.
TIM_DEV_DIR = ['early', 'late']
PIT_DEV_DIR = ['lower', 'higher']

# 02. GENERATE COUNTERBALANCED TRIALS
# Generate all possible combinations of the independent variables.
# This will counterbalance the deviations for their type and direction.
TIM_TARGET_COMBOS1 = [
{"isi" : 500, "dev" : td, "dev_cat" : "timing", "dev_dir" : tdt} for td, tdt in product(TIM_DEV, TIM_DEV_DIR)
] * (par["TIM_DEV_REP"]/2)
TIM_TARGET_COMBOS2 = [
{"isi" : 700, "dev" : td, "dev_cat" : "timing", "dev_dir" : tdt} for td, tdt in product(TIM_DEV, TIM_DEV_DIR)
] * (par["TIM_DEV_REP"]/2)

PIT_TARGET_COMBOS = [
{"dev" : pd, "dev_cat" : "pitch", "dev_dir" : pdt} for pd, pdt in product(PIT_DEV, PIT_DEV_DIR)
] * par["PIT_DEV_REP"]

TARGET_COMBOS = TIM_TARGET_COMBOS + PIT_TARGET_COMBOS
VALID_TARGET_COMBOS = []
for combo in TARGET_COMBOS:
	
	if "timing" in combo["dev_cat"]:
		
		# If DEV > 0, then type cannot be "early".
		if combo["dev"] > 0:
			if combo["dev_dir"] == "early":
				continue

		# If DEV < 0, then type cannot be "late".
		if combo["dev"] < 0:
			if combo["dev_dir"] == "late":
				continue

	if "pitch" in combo["dev_cat"]:
		# If DEV > 0, then type cannot be "lower".
		if combo["dev"] > 0:
			if combo["dev_dir"] == "lower":
				continue

		# If DEV < 0, then type cannot be "higher".
		if combo["dev"] < 0:
			if combo["dev_dir"] == "higher":
				continue

	# If all checks pass, append the trial combo (dict).
	VALID_TARGET_COMBOS.append(combo)

# 03. GENERATE TRIALS PER MRI RUN


COMBOS_RUNS = []
for run in range(par["NO_MRI_RUNS"]):
	
	# Randomly shuffle the deviants
	VALID_TARGETS = VALID_TARGET_COMBOS.copy()
	random.shuffle(VALID_TARGETS)

	# Sample with replacement (allowing repetition)
	TIME_BETWEEN_DEVS = random.choices(
		range(par["TIME_BETWEEN_DEVS_MIN"], par["TIME_BETWEEN_DEVS_MAX"] + 1),
		k=len(VALID_TARGET_COMBOS) - 1 # Trial-level randomization
		)
	ISI = random.choices(
		range(par["ISI_MIN"], par["ISI_MAX"] + 1),
		k=len(VALID_TARGET_COMBOS) # Trial-level randomization
		)
	BASE_FREQ = random.choices(
		range(par["FREQ_MIN"], par["FREQ_MAX"] + 1),
		k=len(VALID_TARGET_COMBOS) # Trial-level randomization
		)
	no_tones_before = random.choices(
		range(3, 6), # starting tones
		k=1 # Run-level randomization
		)[0]
	COMBOS_ALL_DEV = []
	# Loop through each deviants and define other variables.
	for count, trial in enumerate(VALID_TARGETS):
		
		# Calculate number of standard tones in the current and next sequence
		time_until_next_dev = TIME_BETWEEN_DEVS[count]
		isi_next = ISI[count + 1] if count + 1 < len(ISI) else ISI[count]
		min_time_next  = 3 * (par["TONE_DURATION"] + isi_next)
		min_time_after = 2 * (par["TONE_DURATION"] + ISI[count])
		
		if time_until_next_dev < min_time_next + min_time_after:
			# Window is too tight. Force minimums and accept constraint violation.
			no_tones_after  = 2
			no_tones_next = 3
		else:
			# Time available for tones in current chunk
			available_for_after = time_until_next_dev - min_time_next
			max_tones_after = int(np.floor(available_for_after / (par["TONE_DURATION"] + ISI[count])))
			max_tones_after = max(max_tones_after, 2)
			no_tones_after = random.randint(2, max_tones_after)
			
			# Time available for tones in the next chunk
			time_next = time_until_next_dev - (no_tones_after * (par["TONE_DURATION"] + ISI[count]))
			no_tones_next = max(3, int(np.floor(time_next / (par["TONE_DURATION"] + isi_next))))

		# Add values
		trial["dev_abs"] = abs(trial["dev"])
		trial["isi"] = ISI[count]
		trial["base_freq"] = BASE_FREQ[count]
		trial["no_tones_before"] = no_tones_before
		trial["no_tones_after"]  = no_tones_after
		trial["no_tones_next"]   = no_tones_next
		trial["dev_loc"] = no_tones_before + 1
		trial["trial_idx"] = count + 1
		trial["run_idx"] = run + 1
		
		# Append the final structure
		COMBOS_ALL_DEV.append(trial)

		no_tones_before = no_tones_next

	COMBOS_RUNS.append(COMBOS_ALL_DEV)