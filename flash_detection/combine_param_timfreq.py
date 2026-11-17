#! /usr/bin/env python
# Time-stamp: <17-11-2026 m.utrosa@bcbl.eu>
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
from collections import Counter
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
	no_dev_tones = len(VALID_TARGET_COMBOS) # Deviant tones per run
	sequence_length = par["RUN_DURATION_MIN"] * 60 * 1000

	SESSION_EVENTS = []
	UNALLOWED_BASE_FREQ = [] # For tracking already selected fStd
	max_pitDev = False # No max pitch deviant at the session's start
	min_pitDev = False # No min pitch deviant at the session's start
	for run in range(par["NO_MRI_RUNS"]):
		
		# Find all possible solutions given the desired run duration.
		# Note, the actual run duration will be different because here
		# we are not taking into account the randomly-determined GAP
		# between deviant events (there is a max and min no. of std
		# tones between all devs)!
		solutions = []
		for ISI in range(par["ISI_MIN"], par["ISI_MAX"] + 1):
			numerator = sequence_length + ISI
			denominator = par["TONE_DURATION"] + ISI # tone period

			# Ensure we can fit the tone periods within the run
			if numerator % denominator != 0:
				continue

			# How many tone periods can we fit?
			total_tones = numerator // denominator

			if total_tones < no_dev_tones:
				continue

			# The number of standard tone needed for desired run duration
			no_std_tones = total_tones - no_dev_tones
			solutions.append({
				"ISI" : ISI,
				"N_total" : total_tones,
				"N_std" : no_std_tones,
				"N_dev" : no_dev_tones
				})
		
		# Only print update once per session
		if run < 1:
			print("The possible ISI & tone no. per run given input parameters are:"
				f"\n{solutions}.")

		# Determine the ISI, GAPS between deviant events, and the INDICES of deviants.
		ISI_found = False
		TIME_BETWEEN_DEVS = False
		dev_idxs = False
		while not ISI_found or not TIME_BETWEEN_DEVS or not dev_idxs:

			# Find ISI
			ISI = int(random.choices(
				range(par["ISI_MIN"], par["ISI_MAX"] + 1),
				k=1
				)[0])
			numerator = sequence_length + ISI
			tone_period = par["TONE_DURATION"] + ISI
			if numerator % tone_period != 0:
				continue # skip the rest of the iteration

			# The number of tones in current run
			total_tones = numerator // tone_period
			ISI_found = True

			# Find GAPS between deviants: a gap must be an exact number
			# of tone periods so deviants land on tone boundaries.
			valid_gaps = [
				gap for gap in range(par["TIME_BETWEEN_DEVS_MIN"], par["TIME_BETWEEN_DEVS_MAX"] + 1)
				if gap % tone_period == 0
				]

			# If no gap value is a multiple, resample the ISI.
			if not valid_gaps:
				ISI_found = False
				continue

			# Sample with replacement (allowing repetition!)
			# Sampling with repetition could induce a rhythmic pattern.
			TIME_BETWEEN_DEVS = random.choices(
				valid_gaps,
				k = no_dev_tones # No. of deviants in one run.
			)

			# Find indices for deviant tones given the selected ISI and number of tones
			# Rules: the first 3 tones are never deviant.
			# Every deviant tone must be separated by min: par["TIME_BETWEEN_DEVS_MIN"]
			#									  and max: par["TIME_BETWEEN_DEVS_MAX"]
			dev_idxs = []
			tone_period = par["TONE_DURATION"] + ISI

			# The first 3 tones should never be deviant
			if TIME_BETWEEN_DEVS[0] > 3 * tone_period:
				first_dev_idx = int(TIME_BETWEEN_DEVS[0] / tone_period)
			else: # If the first time is smaller than the time for 3 std tones & isi
				first_dev_idx = random.choices(range(4, 6), k=1)[0]

			# Remove the first element as it was decided above
			TIME_BETWEEN_DEVS.pop(0)

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
		fStd_found = False
		while not fStd_found:
			BASE_FREQ = random.choices(
				range(par["FREQ_MIN"], par["FREQ_MAX"] + 1),
				k=1
				)[0]

			# Make sure the fStd is not a deviant from the previous runs
			if BASE_FREQ not in UNALLOWED_BASE_FREQ:
				
				# Current standard should not be deviant of the previous run
				if max_pitDev: # or min_pitDev (equivalent)
					if BASE_FREQ > max_pitDev or BASE_FREQ < min_pitDev:
						fStd_found = True
				else:
					fStd_found = True

		# Track the smallest and largest pitch deviants
		max_pitDev = round(BASE_FREQ * (2 ** max(PIT_DEV)), 1)
		min_pitDev = round(BASE_FREQ * (2 ** min(PIT_DEV)), 1)

		# In a single session, each run has a different standard pitch
		UNALLOWED_BASE_FREQ.append(BASE_FREQ)

		# Print update to terminal/txt
		print(
			f"\n\n~~~ RUN {run + 1} ~~~ \n* ISI: {ISI} ms"
			f"\n* Standard frequency: {BASE_FREQ} Hz"
			f"\n* Min deviant frequency: {min_pitDev} Hz"
			f"\n* Max deviant frequency: {max_pitDev} Hz"
			f"\n* Planned total no. of tones: {total_tones}"
		)
		
		# Randomly shuffle the deviants and copy the deviants that occur per run.
		# This ensures that all deviants occur in one run in a random order.
		VALID_TARGETS = VALID_TARGET_COMBOS.copy()
		random.shuffle(VALID_TARGETS)

		# Calculate the number of standard tones at the end (random) and number of "silent" tones
		# Each "silent" period has the same number of tones but distance between deviants are not
		# constant because this period is inserted into an already determined "gap" between devs.
		no_std_end = random.randint(par["MIN_STD_END"], par["MAX_STD_END"]) # inclusive boundaries
		no_silent_tones = int(np.floor((par["NO_DEV_PERIOD_TIME"] * 1000) / tone_period))
		print(f"* No. of standard tones added to the end of the sequence: {no_std_end}")
		
		# Calculate where is it possible to insert longer periods of standard tones.
		# The silent periods must NOT be close to the start or the end of the sequence.
		mid_silent_idx = int(np.ceil(len(dev_idxs)/par["NO_DEV_PERIOD_REP"]))

		# Silent periods cannot occur on the deviant tone.
		idx_available  = [sia for sia in list(range(mid_silent_idx, dev_idxs[-mid_silent_idx])) if sia not in dev_idxs]
		
		# Silent periods should be separted at min. for double their duration.
		print(f"* Starting standard tones no.: {first_dev_idx - 1}")
		print(f"* Silent tones no.: {no_silent_tones}")
		selected = [first_dev_idx + no_silent_tones] # The first silence is at the start of the sequence
		for silent_ix in idx_available:
			if abs(silent_ix - selected[-1]) >= 2 * no_silent_tones:
				selected.append(silent_ix)
		selected.pop(0) # Now remove the first one because no silence there!

		# Select the final indices for the desired repetition of silent periods.
		silent_idxs = []
		for silence in range(par["NO_DEV_PERIOD_REP"]):
			pick = random.choice(selected)
			silent_idxs.append(pick)
			selected.remove(pick)

		# Create the RUN with one dictionary per tone.
		RUN_EVENTS = []

		# Add silent tones to the start of the sequence.
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
		dev_count = 0
		std_end_count = 0
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
		run_duration = round((len(RUN_EVENTS) * tone_period - ISI) / 60000, 3)
		silent_duration = round((no_silent_tones * tone_period - ISI) / 1000)
		silence_perc = round(((silent_duration/60)/run_duration) * 100, 3)
		print(
			f"\nThe sequence has an actual total of {len(RUN_EVENTS)} tones, resulting in a total "
			f"run duration of {run_duration} min. "
			f"About {silent_duration} sec of it are longer periods of standard tones, "
			f"corresponding to {silence_perc} % of the total run duration."
		)

		# Check for any rhythm or other pattern in deviant positions.
		print(
			"\nThe selected gaps in order:\n"
			f"{TIME_BETWEEN_DEVS}.\n"
			"Is there a rhythmic pattern?\n"
			"\nThe selected deviant indices in order:\n"
			f"{dev_idxs}.\n"
			"Is there a rhythmic pattern?"
		)

		# Append the run to the events of this experimental session.
		SESSION_EVENTS = SESSION_EVENTS + RUN_EVENTS

	# 03. GENERATE FLASH VARIABLES --------------------------------------------
	# Calculate how many flashes are needed per run
	counts = Counter(ev["run_idx"] for ev in SESSION_EVENTS)
	flash_num = {run: int(n * par["FLASH_PROB"]) for run, n in counts.items()}
	
	# Minimum temporal distance between consecutive flash onsets
	flash_distance = (
		par["FLASH_ISI_MAX"] * (par["FLASH_REP_MAX"] - 1)
		+ par["FLASH_DURATION"] * par["FLASH_REP_MAX"] 
		+ par["MAX_RESPONSE_TIME"] + par["MAX_FEEDBACK_TIME"]
	)

	# Pre-compute run boundaries (first and last index per run)
	run_boundaries = {}
	for ix, ev in enumerate(SESSION_EVENTS):
		run = ev["run_idx"]
		if run not in run_boundaries:
			run_boundaries[run] = [ix, ix]  # [start, end]
		else:
			run_boundaries[run][1] = ix
	
	# Pre-identify eligible flash indices per run
	flash_idxs_available = {}
	for ix, ev in enumerate(SESSION_EVENTS):
		run = ev["run_idx"]
		run_start, run_end = run_boundaries[run]

		# No flash on deviant events or the events following the deviant.
		## Check current event
		if pd.isna(ev["dev"]):
			is_standard = True
		else:
			is_standard = False

		## Check previous three events
		prev_was_deviant = False
		if ix - 1 >= run_start and not pd.isna(SESSION_EVENTS[ix - 1]["dev"]):
			prev_was_deviant = True
		elif ix - 2 >= run_start and not pd.isna(SESSION_EVENTS[ix - 2]["dev"]):
			prev_was_deviant = True
		elif ix - 3 >= run_start and not pd.isna(SESSION_EVENTS[ix - 3]["dev"]):
			prev_was_deviant = True

		## Check next three events
		next_is_deviant = False
		if ix + 1 <= run_end and not pd.isna(SESSION_EVENTS[ix + 1]["dev"]):
			next_is_deviant = True
		elif ix + 2 <= run_end and not pd.isna(SESSION_EVENTS[ix + 2]["dev"]):
			next_is_deviant = True
		elif ix + 3 <= run_end and not pd.isna(SESSION_EVENTS[ix + 3]["dev"]):
			next_is_deviant = True

		# Determine if flash is allowed at current iteration
		in_first_three = ix - run_start <= 2
		in_last_one = ix == run_end

		# Find available flash indices
		if is_standard and not prev_was_deviant and not next_is_deviant and not in_first_three and not in_last_one:
			flash_idxs_available.setdefault(run, []).append(ix)
	
	# Initialize all events to no flash
	for ev in SESSION_EVENTS:
		ev["flash_rep"] = np.nan
		ev["flash_isi"] = np.nan
	
	# Pick randomly the indices for flash events
	print(f"\n\n~~~~ FLASH VARIABLES ~~~~: {run}")
	for run in sorted(flash_num.keys()):

		# Get indices available for flashes for current run
		flash_run = flash_num[run]
		flash_idxs_avail_run  = flash_idxs_available.get(run, [])
		if flash_run > len(flash_idxs_avail_run):
			print(f"WARNING: requested {flash_run} flashes but only {len(flash_idxs_avail_run)} positions eligible.")

		# Print to terminal/txt
		print(f"RUN: {run}")
		print(f"Needed flash idxs: {flash_run}")
		print(f"Eligible flash idxs: {len(flash_idxs_avail_run)}")

		# Compute tone period, assuming constant ISI per RUN.
		# ISI is read from SESSION_EVENTS for the current run.
		tone_period = par["TONE_DURATION"] + SESSION_EVENTS[flash_idxs_avail_run[0]]["isi"]

		# Random selection ensuring minimum temporal distance
		selected = []
		pool = list(flash_idxs_avail_run)
		random.shuffle(pool)
		for candidate in pool:
			if len(selected) >= flash_run:
				break
			if all(abs(candidate - idx_selected) * tone_period >= flash_distance for idx_selected in selected):
				selected.append(candidate)

		for idx in selected:
			SESSION_EVENTS[idx]["flash_rep"] = random.randint(1, par["FLASH_REP_MAX"])
			SESSION_EVENTS[idx]["flash_isi"] = random.randint(
				par["FLASH_ISI_MIN"],
				par["FLASH_ISI_MAX"])

		print(f"Selected flash idxs: {len(selected)}\n")

	# 04. BUILD FLASH-ONLY DATAFRAME ------------------------------------------
	FLASH_EVENTS = []
	for tone_ix, se in enumerate(SESSION_EVENTS):
		if not pd.isna(se["flash_rep"]) and not pd.isna(se["flash_isi"]):
			
			# Position of this event within its run (0-based)
			run_start, _ = run_boundaries[se["run_idx"]]
			run_ix = tone_ix - run_start

			# Calculate tone period (can differ per run, depending on ISI)
			tone_period = par["TONE_DURATION"] + se["isi"]

			# Onset of the flash
			onset_time  = run_ix * tone_period + 2 * par["TONE_DURATION"]
			
			# Append a flash event
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