#! /usr/bin/env python
# Time-stamp: <09-11-2026 m.utrosa@bcbl.eu>
'''
References:
Friston, K. J., Zarahn, E. O. R. N. A., Josephs, O., Henson, R. N., & 
Dale, A. M. (1999). Stochastic designs in event-related fMRI. Neuroimage,
10(5), 607-619
'''
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 01. IMPORT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import sys # for session-specific text file summary 
import random
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 02. FUNCTION
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def create_experimental_sessions(par, sesID, save_csv=False, out_path=False):
	
	# 01. GENERATE INDEPENDENT VARIABLES --------------------------------------
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

	# Generate all possible combinations of the independent variables.
	# This will counterbalance the deviations for their type and direction.
	TIM_TARGET_COMBOS = [
	{"dev" : td, "dev_cat" : "timing", "dev_dir" : tdt} for td, tdt in product(TIM_DEV, TIM_DEV_DIR)
	] * par["TIM_DEV_REP"]
	PIT_TARGET_COMBOS = [
	{"dev" : pd, "dev_cat" : "pitch", "dev_dir" : pdt} for pd, pdt in product(PIT_DEV, PIT_DEV_DIR)
	] * par["PIT_DEV_REP"]
	TARGET_COMBOS = TIM_TARGET_COMBOS + PIT_TARGET_COMBOS

	# Remove incorrect cominations
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

	# 02. GENERATE STANDARD TONES ---------------------------------------------
	no_dev_tones = len(VALID_TARGET_COMBOS)
	sequence_length = par["RUN_DURATION_MIN"] * 60 * 1000

	SESSION_EVENTS = []
	for run in range(par["NO_MRI_RUNS"]):
		
		# Find all possible ISI lengths and number of tones given the FIXED run duration.
		solutions = []
		for ISI in range(par["ISI_MIN"], par["ISI_MAX"] + 1):
			numerator = sequence_length + ISI
			denominator = par["TONE_DURATION"] + ISI

			if numerator % denominator != 0:
				continue

			total_tones = numerator // denominator

			if total_tones < no_dev_tones:
				continue

			no_std_tones = total_tones - no_dev_tones
			solutions.append({"ISI" : ISI, "N_total" : total_tones, "N_std" : no_std_tones})
		if run < 1:
			print("The possible ISI values and number of tones given input parameters are:"
				f"\n{solutions}.")

		# Determine the ISI, GAPS between deviant events, and the INDICES of deviants.
		ISI_found = False
		TIME_BETWEEN_DEVS = False
		dev_idxs = False
		while not ISI_found or not TIME_BETWEEN_DEVS or not dev_idxs:

			# Reset the iteration if not found
			ISI_found = False
			TIME_BETWEEN_DEVS = False
			dev_idxs = False

			# Find ISI
			ISI = int(random.choices(
				range(par["ISI_MIN"], par["ISI_MAX"] + 1),
				k=1
				)[0])
			numerator = sequence_length + ISI
			tone_period = par["TONE_DURATION"] + ISI
			if numerator % tone_period != 0:
				continue

			total_tones = numerator // tone_period
			ISI_found = True

			# Find GAPS between deviants
			# A gap must span an exact number of tone periods so deviants land
			# on tone boundaries. Keep only gap values in the allowed range that
			# are exact multiples of the tone period (tone duration + ISI).
			valid_gaps = [
				gap for gap in range(par["TIME_BETWEEN_DEVS_MIN"], par["TIME_BETWEEN_DEVS_MAX"] + 1)
				if gap % tone_period == 0
				]

			# If no gap value in the range is a clean multiple, current ISI can't
			# satisfy the constraint, so resample the ISI.
			if not valid_gaps:
				ISI_found = False
				continue

			# Sample with replacement (allowing repetition), no rhythmic pattern.
			TIME_BETWEEN_DEVS = random.choices(
				valid_gaps,
				k = no_dev_tones
			)

			# Find indices for deviant tones given the selected ISI and number of tones
			# Rules: the first 3 tones are not deviant
			# Every deviant tone must be separated by min: par["TIME_BETWEEN_DEVS_MIN"]
			#									  and max: par["TIME_BETWEEN_DEVS_MAX"]
			# The spacing between deviant events has to be randomly selected without any
			# order or rhythmicity or other repeating pattern.
			dev_idxs = []
			tone_period = par["TONE_DURATION"] + ISI

			# The first 3 tones should never be deviant
			if TIME_BETWEEN_DEVS[0] > 3 * tone_period:
				first_dev_idx = int(TIME_BETWEEN_DEVS[0] / tone_period)
				TIME_BETWEEN_DEVS.pop(0)
			else:
				first_dev_idx = random.choices(range(4, 6), k=1)[0]

			# Build cumulative indices from the first deviant + sampled gaps
			dev_idxs = [first_dev_idx]
			for gap in TIME_BETWEEN_DEVS:
				no_tones_in_gap = int(gap / tone_period)
				current_idx = dev_idxs[-1] + no_tones_in_gap
				dev_idxs.append(current_idx)

			# Last index must be smaller than index of the last tone in the sequence
			if dev_idxs[-1] < total_tones:
				pass # valid
			else:
				dev_idxs = False # invalid, resample

		# Determine the STANDARD FREQUENCY
		BASE_FREQ = random.choices(
			range(par["FREQ_MIN"], par["FREQ_MAX"] + 1),
			k=1
			)[0]

		# Print update to terminal/txt
		print(
			f"\n\n~~~ RUN {run + 1} ~~~ \n* ISI: {ISI} ms"
			f"\n* Standard frequency: {BASE_FREQ} Hz"
			f"\n* Planned total no. of tones: {total_tones}"
		)

		# Randomly shuffle the deviants and copy the deviants that occur per run.
		# This ensures that all timing and pitch deviants occur in one run.
		VALID_TARGETS = VALID_TARGET_COMBOS.copy()
		random.shuffle(VALID_TARGETS)

		# Create the RUN with one dictionary per tone and add silent periods.
		RUN_EVENTS = []
		dev_count = 0
		std_end_count = 0
		no_std_end = random.randint(par["MIN_STD_END"], par["MAX_STD_END"]) # inclusive boundaries
		no_silent_tones = int(np.floor((par["NO_DEV_PERIOD_TIME"] * 1000) / tone_period))
		print(f"* No. of standard tones added to the end of the sequence: {no_std_end}")
		
		# Calcualte where is it possible to insert longer periods of standard tones
		# The silent periods must NOT be close to the start or the end of the sequence
		mid_silent_idx = int(np.ceil(len(dev_idxs)/par["NO_DEV_PERIOD_REP"]))

		# Silent periods cannot occur on the deviant tone
		idx_available  = [sia for sia in list(range(mid_silent_idx, dev_idxs[-mid_silent_idx])) if sia not in dev_idxs]
		
		# Silent periods should be separted at min. for double their duration
		print(f"* Starting standard tones no.: {first_dev_idx - 1}")
		print(f"* Silent tones no.: {no_silent_tones}")
		selected = [first_dev_idx + no_silent_tones] # The first silence is at the start of the sequence
		for silent_ix in idx_available:
			if abs(silent_ix - selected[-1]) >= 2 * no_silent_tones:
				selected.append(silent_ix)

		# Select the final indices for the desired repetition of silent periods
		silent_idxs = []
		for silence in range(par["NO_DEV_PERIOD_REP"]):
			pick = random.choice(selected)
			silent_idxs.append(pick)
			selected.remove(pick)
		print(
			"\nLonger periods of standard tones, equivalent to the silent events, "
			f"are added at positions: {sorted(silent_idxs)}. "
			f"These periods are {par['NO_DEV_PERIOD_TIME']} seconds long and "
			f"correspond to {no_silent_tones} standards."
		)

		# Add silent tones to the start of the sequence
		for silence in range(no_silent_tones):
			event = {
				'dev': np.nan,
				'dev_cat': None,
				'dev_dir': None,
				'dev_abs': np.nan,
				'dev_no' : np.nan,
				'isi': ISI,
				'base_freq': BASE_FREQ,
				'run_idx'  : run + 1
			}
			RUN_EVENTS.append(event)

		# Iterate through all sequence tones
		for tone_idx in range(total_tones):
			
			# Count of tones starting with 1
			tone = tone_idx + 1

			# If we're at "silent" period index, add that period.
			if tone in silent_idxs:
				for silence in range(no_silent_tones):
					event = {
						'dev': np.nan,
						'dev_cat': None,
						'dev_dir': None,
						'dev_abs': np.nan,
						'dev_no' : np.nan,
						'isi': ISI,
						'base_freq': BASE_FREQ,
						'run_idx'  : run + 1
					}
					RUN_EVENTS.append(event)
			
			# Add deviant if at the deviant's index.
			if tone in dev_idxs:

				# Add values to deviant event
				event = VALID_TARGETS[dev_count].copy()
				event["dev_abs"] = abs(event["dev"])
				event["dev_no"]  = dev_count + 1 # consecutive number of the deviant tone
				event["isi"] = ISI
				event["base_freq"] = BASE_FREQ
				event["run_idx"] = run + 1

				# Add the deviant event info to run info
				RUN_EVENTS.append(event)

				# Update the deviations count
				dev_count += 1

			# If not at deviant's or silent's index, add a single standard tone
			else:
				event = {
						'dev': np.nan,
						'dev_cat': None,
						'dev_dir': None,
						'dev_abs': np.nan,
						'dev_no' : np.nan,
						'isi': ISI,
						'base_freq': BASE_FREQ,
						'run_idx'  : run + 1
					}
				
				# Add a standard tone only until if not all deviants added
				if dev_count < len(dev_idxs):
					RUN_EVENTS.append(event)
				
				# Decide randomly (from range) how many standard tones to end with
				else:
					# Truncate the sequence to a limited number of standard tones
					if std_end_count < no_std_end:
						RUN_EVENTS.append(event)
						std_end_count += 1

		# Once we are at the end, add a "silent" period. 
		for silence in range(no_silent_tones):
			event = {
				'dev': np.nan,
				'dev_cat': None,
				'dev_dir': None,
				'dev_abs': np.nan,
				'dev_no' : np.nan,
				'isi': ISI,
				'base_freq': BASE_FREQ,
				'run_idx'  : run + 1
			}
			RUN_EVENTS.append(event)

		# Print update to terminal/txt
		run_duration = round((len(RUN_EVENTS) * tone_period - ISI) / 60000, 2)
		silent_duration = round((no_silent_tones * tone_period - ISI) / 1000)
		silence_perc = round(((silent_duration/60)/run_duration) * 100, 2)
		print(
			f"\nThe sequence has an actual total of {len(RUN_EVENTS)} tones, resulting in a total "
			f"run duration of {run_duration} min. "
			f"About {silent_duration} sec of it are longer periods of standard tones, "
			f"corresponding to {silence_perc} % of the total run duration."
		)

		# Append the run to the events of this experimental session
		SESSION_EVENTS = SESSION_EVENTS + RUN_EVENTS

	# 03. GENERATE FLASH VARIABLES --------------------------------------------
	# Iterate through each dictionary, representing an event in an exp. session.
	previous_was_flash = False	
	for ix, ev in enumerate(SESSION_EVENTS):

		# Ensure: no flash on deviant events or the events following the deviant.
		# Check current event
		if pd.isna(ev["dev"]):
			is_standard = True
		else:
			is_standard = False

		# Check previous event
		if ix > 0:
			if not pd.isna(SESSION_EVENTS[ix - 1]["dev"]):
				prev_was_deviant = True
			else:
				prev_was_deviant = False
		else:
			prev_was_deviant = False

		# Determine if flash is allowed at current iteration
		in_first_three = ix <= 2
		in_last_one = ix == len(SESSION_EVENTS) - 1

		# Generate flash characteristics
		if (
			is_standard
			and not prev_was_deviant
			and not in_first_three
			and not in_last_one
			and not previous_was_flash
		):
			if random.random() < par["FLASH_PROB"]:
				FLASH_REP = random.randint(1, par["FLASH_REP_MAX"])
				FLASH_ISI = random.randint(
					par["FLASH_ISI_MIN"],
					par["FLASH_ISI_MAX"])
				previous_was_flash = True
			else:
				FLASH_REP = np.nan
				FLASH_ISI = np.nan
				previous_was_flash = False
		else:
			FLASH_REP = np.nan
			FLASH_ISI = np.nan
			previous_was_flash = False

		ev["flash_rep"] = FLASH_REP
		ev["flash_isi"] = FLASH_ISI

	# 04. BUILD FLASH-ONLY DATAFRAME ------------------------------------------
	FLASH_EVENTS = []
	flash_distance = (
		par["FLASH_ISI_MAX"] * (par["FLASH_REP_MAX"] - 1)
		+ par["FLASH_DURATION"] * par["FLASH_REP_MAX"] 
		+ par["MAX_RESPONSE_TIME"] + par["MAX_FEEDBACK_TIME"]
	)
	last_onset = -flash_distance
	for tone_ix, se in enumerate(SESSION_EVENTS):
		if not pd.isna(se["flash_rep"]) or not pd.isna(se["flash_isi"]):
			
			# Calculate tone period (can differ per run, depending on ISI)
			tone_period = par["TONE_DURATION"] + se["isi"]

			# Onset of the flash must occur within the ISI of the tone
			# at least "TONE_DURATION" time after the tone has ended for 
			# perceptual separability between audio & visual stimuli.
			onset_time  = tone_ix * tone_period + 2 * par["TONE_DURATION"]
			
			# If minimum distance between consecutive flash events is not
			# met, move to the next iteration.
			if onset_time - last_onset < flash_distance:
				continue
			
			# Append a flash event if minimum distance ensured
			flashing_duration = (
				(se["flash_rep"] - 1) * se["flash_isi"]
				+ se["flash_rep"] * par["FLASH_DURATION"]
			)
			FLASH_EVENTS.append({
				"onset"    : onset_time,
				"duration" : flashing_duration,
				"n_reps"   : se["flash_rep"],
				"isi"      : se["flash_isi"],
				"run_idx"  : se["run_idx"]
			})

			# Update variable
			last_onset = onset_time

	# 05. SAVE TRIALS ---------------------------------------------------------
	# Create a dataframe from the list of dictionaries
	TONES_DF = pd.DataFrame(SESSION_EVENTS)
	FLASH_DF = pd.DataFrame(FLASH_EVENTS)
	
	# Save the dataframe as a .csv file
	if save_csv:
		out_path.mkdir(exist_ok=True, parents=True)

		# TONES DF
		tones_fnm =  f"ses-{sesID:003d}_exp_parameter_combo.csv"
		out_dir   = out_path / tones_fnm
		TONES_DF.to_csv(out_dir, sep=",", index=False)

		# FLASH DF
		flash_fnm =  f"ses-{sesID:003d}_exp_distractor_combo.csv"
		out_dir   = out_path / flash_fnm
		FLASH_DF.to_csv(out_dir, sep=",", index=False)

		# Print update to terminal/txt
		print(f"\nSaved {tones_fnm} and {flash_fnm} to {out_path}.")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 03. SIMULATION OF EXPERIMENTAL SESSIONS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":

	# Import configuration
	from config_timfreq import params
	import config_timfreq as c

	# Ask for user-defined parameters
	sim = input("How many experimental sessions to simulate:")
	simID = int(sim)

	# Simulate
	for session in range(1, simID + 1):
		with open(
			c.outPath / f"ses-{session:003d}_exp_parameter_combo.txt",
			"w"
			) as f:
			sys.stdout = f
			create_experimental_sessions(params, session, True, c.outPath)