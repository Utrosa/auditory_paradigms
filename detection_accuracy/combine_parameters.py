#! /usr/bin/env python
# Time-stamp: <2026-04-27 m.utrosa@bcbl.eu>

# 00. PREPARATION ---------------------------------------------------------------------------------
import sys
import random
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product

# 01. DEFINE FUNCTIONS  ---------------------------------------------------------------------------
def create_deviations(num_values, min_val, max_val, zero=True, N=100):
	"""
	Generate `num_values` unique integers by sampling from a pool of log-spaced values (base 10).
	Sampling is random and without replacement.

	Parameters
	----------
	num_values (int): The total number of deviations desired.
	min_val (int): The smallest deviation in absolute terms. Must be larger than 0.
	max_val (int): The largest deviation in absolute terms.
	zero (bool): If True, includes 0 in the resulting deviation sample.
	N (int): The multiplier for the log-spaced pool size. Higher values are better.
	
	Returns
	-------
	selected_values (list of int): A sorted list of unique integer from a log space.
	
	Raises
	------
	ValueError:
		- if `min_val` <= 0
		- if `max_val` <= `min_val`, or
		- if the log pool cannot provide `num_values` unique integers.

	Notes
	-----
	Why logarithmic? 
	Human perception of magnitude is non-linear and logarithmic (Weber & Fechner).

	Relevant: 10.1126/science.1156540.
	- Innate intuition of number mapping is on a logarithmic scale.
	- The concept of linear number line is a cultural invention.
	- Linear mapping is observed only for small/symbolic numbers in educated participants.
	"""
	# Validate input arguments
	if min_val <= 0:
		raise ValueError("min_val must be greater than 0 for log10 calculation.")
	if max_val <= min_val:
		raise ValueError("max_val must be greater than min_val.")

	# Generate a pool of logarithmically spaced numbers
	log_pool = np.logspace(
		start = np.log10(min_val),
		stop  = np.log10(max_val),
		num   = num_values * N,
		endpoint=False
		)

	# Round, convert to int, and select unique values only
	int_values = np.unique(np.round(log_pool).astype(int))
	
	# Raise error if not possible to meet input arguments
	if len(int_values) < num_values:
		raise ValueError(
		f"Cannot generate {num_values} unique values. "
		f"Log-spaced pool size is {len(int_values)}. "
		"Try increasing the N multiplier or decreasing num_values."
		)

	# Randomly sample unique values
	if zero:
		# Sample one less than `num_values` because we're adding zero
		selected_values = np.random.choice(list(int_values), size=num_values-1, replace=False)
		# Add zero
		result = np.concatenate([[0], selected_values])

	else:
		result = np.random.choice(list(int_values), size=num_values, replace=False)

	return np.sort(result).tolist()

def calculate_trial_duration(combo, params):
	"""
	Calculates a theoretical trial duration in milliseconds.
	
	combo:  a dictionary with information about the trial's ITI and ISI
	params: a dictionary with fixed input parameters (number of tones and their duration)
	"""
	tone_duration = combo["no_tones"] * params["TONE_DURATION"]
	isi_duration  = (combo["no_tones"] - 1) * combo["isi"]
	iti_duration  = combo["iti"]
	trial_duration = tone_duration + isi_duration + iti_duration
	
	return trial_duration

def create_experimental_sessions(params, sesID, save_csv=False, MAX_BLOCK_DURATION_MIN=15):
	"""
	Calculates all parameters required to construct trial sequences for a single 
	experimental session. Counterbalances timing deviations and their locations 
	within tone sequences and randomizes all other variables.

	Parameters
	----------
	params : dict
	    Dictionary containing experiment configuration. Expected keys:
	    
	    **Path & Structure**
	    - "OUT_PATH" : str
	      Path where to save the output files.
	    - "NO_BLOCKS" : int
	      Number of blocks (equal to the number of functional scans in the MRI protocol).
	    
	    **Timing & Intervals**
	    - "ITI_MIN" : int
	      Minimum Inter-Trial Interval (msec). Must be > max(ISI) + tone_duration.
	    - "ITI_MAX" : int
	      Maximum Inter-Trial Interval (msec). Must be < inter-block-interval 
	      (max rest time = 2 min).
	    - "TONE_DURATION" : int
	      Duration of a single tone in msec.
	    - "ISI_MIN" / "ISI_MAX" : int
	      Range of Inter-Stimulus Intervals (msec).
	    - "ISI_STEP" : int
	      Step size of the ISI range (population). 
	      *Note: May be obsolete for MRI, but required for behavioral tasks.*
	    
	    **Sequence Logic**
	    - "MIN_TONES" / "MAX_TONES" : int
	      Minimum and maximum number of tones in a single sequence.
	    - "DEVS" : list
	      Absolute timing deviants in msec.
	    - "DEV_REP" : int
	      How many times each timing deviation must repeat across the session.
	    - "FIRST_DEV_LOC" / "LAST_DEV_LOC" : int
	      Range of tone indices that can be displaced timing-wise.
	    
	    **Frequency Deviations**
	    - "FREQS" : int
	      Absolute frequency deviants in Hz.
	    - "FREQ_REP_MAX" : int
	      Maximum number of frequency deviations allowed per trial.
	    - "FIRST_FREQ_LOC" / "LAST_FREQ_LOC" : int
	      Range of tone indices that can be displaced frequency-wise.

	sesID : int
	    Unique identifier for the current experimental session.
	save_csv : bool
	    If True, the generated trial parameters are saved to a .csv file.
	MAX_BLOCK_DURATION_MIN : int
	    The maximum recommended duration (in minutes) for a single block.

	Returns
	-------
	pd.DataFrame
	    A dataframe containing the generated trial parameters with columns:
	    dev, dev_type, dev_loc, dev_abs, isi, no_tones, base_freq, freq_dev, 
	    freq_dev_type, freq_loc, freq_dev_no, trial_no, block_no, iti, freq_diff, 
	    freq_diff_abs.

	Raises
	------
	ValueError
	    If constraints are violated:
	    - Not enough locations for frequency deviants relative to sequence length.
	    - ITI is too small relative to ISI and tone duration.
	    - Silent/sound trial distribution cannot be evenly split across blocks.
	    - Silent block constraints (no consecutive silent blocks) cannot be met.
	    - Calculated trial durations result in negative values.
	UserWarning
	    If the calculated average block duration exceeds `MAX_BLOCK_DURATION_MIN`.

	Notes
	-----
	- **Inclusivity**: All duration values are corrected for exclusiveness (+ 1).
	- **Silent Trials**: 1/3 of all trials are silent by design. 
	  *Constraints*: First/last trial of a block cannot be silent; no two silent 
	  blocks can occur consecutively.
	- **Constant vs. Variable**: Tone count and ISI duration are constant. 
	  ITI is sampled randomly without replacement.
	- **Deviation Logic**: Frequency deviations never occur on the same tone or 
	  the immediately following tone as a time deviant.
	"""
	# 01. GENERATE INDEPENDENT VARIABLES: Timing deviation size and location ----------------------
	# Create negative values of tone's timing deviation. If applicable, includes a "negative" zero.
	DEV_pos = np.array(params["DEVS"])
	DEV_neg = -DEV_pos

	# Combine positive and negative values into a sorted list.
	DEV_arr = np.concatenate([DEV_pos, DEV_neg])
	DEV     = np.sort(DEV_arr).tolist()

	# Define possible "types" of timing deviations.
	if 0 in DEV:
		DEV_TYPE = ['on_time', 'early', 'late']
	else:
		DEV_TYPE = ['early', 'late']

	# Create a list of locations (tone indices) of the timing deviations in the tone sequences.
	DEV_LOC = list(range(params["FIRST_DEV_LOC"], params["LAST_DEV_LOC"] + 1))

	# 02. GENERATE COUNTERBALANCED TRIALS ---------------------------------------------------------
	# Generate a list of dictionaries with all possible combinations of the independent variables.
	# This will counterbalance the timing deviations for their type and location.
	TARGET_COMBOS = [
	{"dev" : d, "dev_type" : dt, "dev_loc" : dl} for d, dt, dl in product(DEV, DEV_TYPE, DEV_LOC)
	]

	# Remove invalid trial combinations.
	VALID_TARGET_COMBOS = []
	for combo in TARGET_COMBOS:

		# If DEV == 0, then DEV_TYPE must be "on_time".
		if combo["dev"] == 0:
			if combo["dev_type"] != "on_time":
				continue

		# If DEV != 0, then DEV_TYPE cannot be "on_time".
		if combo["dev"] != 0:
			if combo["dev_type"] == "on_time":
				continue

		# If DEV > 0, then type cannot be "early".
		if combo["dev"] > 0:
			if combo["dev_type"] == "early":
				continue

		# If DEV < 0, then type cannot be "late".
		if combo["dev"] < 0:
			if combo["dev_type"] == "late":
				continue

		# Change the dev_loc for on_time combos
		if combo["dev_type"] == "on_time":
			combo["dev_loc"] = np.nan
			print(combo)

		# If all checks pass, appen the trial combo (dict).
		VALID_TARGET_COMBOS.append(combo)

	# Repeat the counterbalanced trials params["DEV_REP"]-times.
	VALID_TARGET_COMBOS_REPS = VALID_TARGET_COMBOS * params["DEV_REP"]
	
	# Calculate required number of silent trials (1/3 of all trials).
	NO_SOUND_TRIALS  = len(VALID_TARGET_COMBOS_REPS)
	NO_SILENT_TRIALS = int((NO_SOUND_TRIALS * (1 / 3))/(2/3))
	NO_TRIALS_ALL    = NO_SOUND_TRIALS + NO_SILENT_TRIALS
	
	# Print updates on the trial count.
	if 0 in DEV:
		print(
			f"\nThere is a total of {NO_SOUND_TRIALS} signal trials."
			f" These trials contain {params['DEV_REP']} repetitions of each timing deviation"
			f" for each possible position of the deviation {DEV_LOC}."
			f" There are {len(DEV)} unique timing deviation values (including zero)."
			f"\n\nAn MRI experiment would have {NO_TRIALS_ALL} trials in total. "
			f"One third (n = {NO_SILENT_TRIALS}) silent (no signal) trials and "
			f"two thirds (n = {NO_SOUND_TRIALS}) sound (signal) trials."
		)
	else:
		print(
			f"\nThere is a total of {NO_SOUND_TRIALS} signal trials."
			f" These trials contain {params['DEV_REP']} repetitions of each timing deviation"
			f" for each possible position of the deviation {DEV_LOC}."
			f" There are {len(DEV)} unique timing deviation values (excluding zero)."
			f"\n\nAn MRI experiment would have {NO_TRIALS_ALL} trials in total. "
			f"One third (n = {NO_SILENT_TRIALS}) silent (no signal) trials and "
			f"two thirds (n = {NO_SOUND_TRIALS}) sound (signal) trials."
		)

	# 03. ADD ALL OTHER VARIABLES -----------------------------------------------------------------
	# We're not interested in the effect of these variables, so we either keep them constant or 
	# randomly vary them on trial-level. This keeps our dependent variable either affected
	# systematically or unaffected.
	
	# Check that the frequency deviancy parameters were set correctly.
	# Rule: frequency deviants cannot occur on the same (n) or the following (n+1) tone on which
	# the timing deviant occurs. 
	# This means there must be enough locations (tone indices) for frequency deviants given
	# the desired number of frequency deviants and the length of tone sequence (total tones).
	if params["FREQ_REP_MAX"] > params["LAST_FREQ_LOC"] - params["FIRST_FREQ_LOC"] - 1:
		raise ValueError(
				f'Frequency deviants cannot occur {params["FREQ_REP_MAX"]}-times per trial '
				f'because there are only '
				f'{params["LAST_FREQ_LOC"] - params["FIRST_FREQ_LOC"] - 1} '
				'positions allowed.\n Adjust input parameters.'
		)
	
	### ----------------------- Parameters that are constant across trials ------------------------
	# Depending on how input parameters are set, these can:
	# 	- be fixed for each experimental session, or
	#	- can vary randomly across experimental sessions. 
	# In both cases, these parameters are fixed for all trials in one experimental session.
	# To make these parameters vary on trial-level, replace "k" with the TOTAL trial number.
	
	# Sample without replacement: every value is unique.
	ISI = random.sample(
		range(params["ISI_MIN"], params["ISI_MAX"] + 1),
		k=1 # For trial-level randomization: k=NO_TRIALS_ALL
		)
	NO_TONES = random.sample(
		range(params["MIN_TONES"], params["MAX_TONES"] + 1),
		k=1 # For trial-level randomization: k=NO_TRIALS_ALL
		)

	### --------------------------- Parameters that vary across trials ----------------------------
	ITI = random.sample(
		range(params["ITI_MIN"], params["ITI_MAX"] + 1),
		k=(NO_TRIALS_ALL)
		)

	# Print update on distance between important events given the average ITI duration.
	# Important events are timing deviations.
	ITI_average = np.mean(ITI)
	min_tones = (NO_TONES[0] - max(DEV_LOC)) + min(DEV_LOC)
	max_tones = (NO_TONES[0] - min(DEV_LOC)) + max(DEV_LOC)
	min_distance = (min_tones * params["TONE_DURATION"] + (min_tones - 1) * ISI[0] + ITI_average) / 1000
	max_distance = (max_tones * params["TONE_DURATION"] + (max_tones - 1) * ISI[0] + ITI_average) / 1000
	print(
		f"\nThe average ITI is {ITI_average:.2f} msec."
		f"\n* The min. distance between timing deviations is {min_distance:.2f} sec."
		f"\n* The max. distance between timing deviations is {max_distance:.2f} sec."
		)

	# Checks to ensure trial separability (perceptual)
	## The smallest ITI must be longer than 2 x (max(ISI) + tone duration).
	if min(ITI) <= 2 * (max(ISI) + params["TONE_DURATION"]):
		raise ValueError(
				f'Min ITI ({min(ITI)} ms) is too short given the '
				f'max ISI ({max(ISI)} ms) and '
				f'tone duration ({params["TONE_DURATION"]} ms).'
		)

	## The smallest ITI must be longer than the longest DEV.
	if min(ITI) <= max(DEV_pos):
		raise ValueError(
				f'Min ITI ({min(ITI)} ms) is too short given the '
				f'max DEV ({max(DEV_pos)} ms).'
		)

	# Loop through each counterbalanced trial and add all other variables.
	COMBOS_ALL_DEV = []
	for count, trial in enumerate(VALID_TARGET_COMBOS_REPS):

		# Add the absolute value of the timing deviant, ISI, and no. of tones.
		trial["dev_abs"]  = abs(trial["dev"])
		trial["isi"]      = ISI[0]
		trial["no_tones"] = NO_TONES[0]
		
		# Create a copy of all possible frequency values.
		FREQ = params["FREQS"].copy()

		# Randomly select one frequency standard and add to trial.
		BASE_FREQUENCY = random.sample(FREQ, 1)
		trial["base_freq"] = BASE_FREQUENCY[0]

		# Remove the standard as a possible frequency deviation.
		FREQ.remove(BASE_FREQUENCY[0])

		# Generate a list of all possible frequency deviation locations in the tone sequence.
		FREQ_LOC_ALL = list(range(params["FIRST_FREQ_LOC"], params["LAST_FREQ_LOC"] + 1))
		
		# Ensure that the dev_loc and freq_loc are not the same for trials with timing devs.
		if not np.isnan(trial["dev_loc"]): # Location for "on-time" trials is np.nan
			FREQ_LOC_ALL.remove(trial["dev_loc"])

		# Ensure freq_loc is not on dev_loc + 1 tone, which is displaced due to relative timing.
		# e.g.: for early tones, the 'create_soundtrack_soundgen.py' shortens the ISI before 
		# the displaced tone and lengthens the ISI after that tone.
		if not np.isnan(trial["dev_loc"]): # Location for "on-time" trials is np.nan
			FREQ_LOC_ALL.remove(trial["dev_loc"] + 1)

		# Randomly determine the number of frequency deviants for the current trial.
		FREQ_REP = random.sample(
			list(range(params["FREQ_REP_MAX"] + 1)),
			1
			)
		
		# Allow random sampling with replacement for deviants.
		FREQ_DEVS = random.choices(
			FREQ,
			k=FREQ_REP[0]
			)

		# Determine the "type" of sampled frequency deviants (> or < than base freq).
		FREQ_DEV_TYPE = []
		for fdt in FREQ_DEVS:
			if fdt < BASE_FREQUENCY[0]:
				FREQ_DEV_TYPE.append("lower")
			else:
				FREQ_DEV_TYPE.append("higher")
		
		# Randomly choose the location of the FREQ_DEVS (without replacement).
		FREQ_LOC = random.sample(FREQ_LOC_ALL, FREQ_REP[0])

		# Add to current trial.
		# If there are no FREQ_DEVS in the current trial (FREQ_REP == 0),
		# add "False" lists.
		if bool(FREQ_DEVS) == True:
			trial["freq_dev"]      = FREQ_DEVS
			trial["freq_dev_type"] = FREQ_DEV_TYPE
			trial["freq_loc"]      = sorted(FREQ_LOC)
			trial["freq_dev_no"]   = len(FREQ_DEVS)
		else:
			trial["freq_dev"]      = [False]
			trial["freq_dev_type"] = ["standard"]
			trial["freq_loc"]      = [False]
			trial["freq_dev_no"]   = len(FREQ_DEVS)
		
		# Append the final structure.
		COMBOS_ALL_DEV.append(trial)

	# Randomly shuffle sound trials.
	random.shuffle(COMBOS_ALL_DEV)

	# 04. CREATE SILENT TRIALS and SPLIT INTO BLOCKS ----------------------------------------------
	# Calculate the number of silent trials needed per block.
	silent_base   = NO_SILENT_TRIALS // params["NO_BLOCKS"]
	silent_rest   = NO_SILENT_TRIALS % params["NO_BLOCKS"]
	silent_trials = [silent_base + 1] * silent_rest + [silent_base] * (params["NO_BLOCKS"] - silent_rest)
	
	# Calculate the number of sound trials needed per block.
	sound_base   = NO_SOUND_TRIALS // params["NO_BLOCKS"]
	sound_rest   = NO_SOUND_TRIALS % params["NO_BLOCKS"]
	sound_trials = [sound_base + 1] * sound_rest + [sound_base] * (params["NO_BLOCKS"] - sound_rest)
	
	# Calculate the number of total trials per block given sound and silent trials.
	blocks     = [sound + silence for sound, silence in zip(sound_trials, silent_trials)]
	block_base = sum(blocks) // params["NO_BLOCKS"]
	remainder  = sum(blocks) % params["NO_BLOCKS"]

	# Print update on the how all trials are split into blocks.
	print(
	f"\nThere will be {silent_base} silent trials per block inserted in the experiment. "
	f"\n{[f'Block {idx + 1}: {slt}' for idx, slt in enumerate(silent_trials)]}."
	f"\n\nThere will be {sound_base} sound trials per block inserted in the experiment. "
	f"\n{[f'Block {idx + 1}: {sdt}' for idx, sdt in enumerate(sound_trials)]}."
	f"\n\nThere will be a total of {block_base} trials per block in the experiment. "
	f"\n{[f'Block {idx + 1}: {b}' for idx, b in enumerate(blocks)]}."
	)

	# Verify the distribution of trials.
	for i in range(params["NO_BLOCKS"]):
		if silent_trials[i] + sound_trials[i] != blocks[i]:
			raise ValueError(f"Block {i + 1} has an issue.")
	if sum(blocks) != NO_TRIALS_ALL:
		raise ValueError(f"Blocks have {blocks} trials, experiment {NO_TRIALS_ALL}.")
	
	# Create one empty/silent trial.
	empty_trial = {
		'dev': None,
		'dev_type': None,
		'dev_loc': None,
		'dev_abs': None,
		'no_tones': NO_TONES[0],
		'isi': ISI[0],
		'base_freq': None, # Irrelevant: not used in create_soundtrack_soundgen.py
		'freq_dev': None,
		'freq_dev_type': None,
		'freq_loc': None,
		'freq_dev_no': None
	}

	# Add silent trials randomly
	block_start_idx = 0
	for block_size, no_silent_trials, no_sound_trials in zip(blocks, silent_trials, sound_trials):

		# Calculate end-exclusive index of the sound block
		sound_block_end_idx = block_start_idx + no_sound_trials
		block_end_idx = block_start_idx + no_sound_trials + no_silent_trials

		last_available  = block_end_idx - 1   # second-to-last
		first_available = block_start_idx + 1 # second

		# Keep track of chosen & forbidden indices
		not_available = []
		idx_chosen = []

		for e_trial in range(no_silent_trials):
			available = list(range(first_available, last_available))
		
			# Remove taken & forbidden indices out of the available ones
			if e_trial != 0:
				for not_avail in not_available:
					if not_avail in available:
						available.remove(not_avail)
						if not available:
							raise ValueError("No valid indices left (constraints too tight)")

			# Chose from allowed indices
			choice = random.choice(available) 
			
			# Empty trials cannot occur in a row
			choice_after  = choice + 1
			choice_before = choice - 1
			
			# Keep track
			idx_chosen.append(choice)
			not_available.append(choice)
			not_available.append(choice_after)
			not_available.append(choice_before)

		# Add empty trials in reverse
		for idx_c in sorted(idx_chosen):
			COMBOS_ALL_DEV.insert(idx_c, empty_trial.copy())

		# Verify block starts correctly
		if COMBOS_ALL_DEV[block_start_idx].get("dev") is None:
			raise ValueError("The block starts with a silent trial.")
		
		# Verify that the block ends with a sound trial.
		if COMBOS_ALL_DEV[block_end_idx - 1].get("dev") is None:
			raise ValueError("The block ends with a silent trial.")
		
		# Update count for next block
		block_start_idx = sound_block_end_idx + no_silent_trials

	# Split trials into blocks
	BLOCK_COMBOS = []
	for block_no, block in enumerate(blocks):
		for trial_no in range(block):

			cad = COMBOS_ALL_DEV.pop(0).copy()

			# Add trial and block ID
			cad["trial_no"] = trial_no + 1
			cad["block_no"] = block_no + 1

			# Add ITI
			cad["iti"] = ITI.pop(0)
			
			BLOCK_COMBOS.append(cad)

	# 06. CALCULATE DURATIONS ---------------------------------------------------------------------
	# Get duration of trials
	trial_durs = []
	for b in BLOCK_COMBOS:
		t_dur = calculate_trial_duration(b, params)
		trial_durs.append(t_dur)
	
	# Get duration of blocks
	block_durations = {b: 0 for b in set(cb["block_no"] for cb in BLOCK_COMBOS)}
	for b, duration in zip(BLOCK_COMBOS, trial_durs):
		b_no = b["block_no"]
		block_durations[b_no] += duration

	# Get average duration of trials & blocks
	block_dur_avg = np.mean(list(block_durations.values()))
	trial_dur_avg = np.mean(trial_durs)
	trial_dur_sec = int(trial_dur_avg / 1000)

	# Convert to min
	block_dur_min = block_dur_avg / 60000
	exp_dur_min   = sum(list(block_durations.values())) / 60000

	# Raise warning if average block duration is too long
	if block_dur_min > MAX_BLOCK_DURATION_MIN:
		warning_msg = (
		f"WARNING: The average block duration ({block_dur_min:.2f} min) "
		f"exceeds the recommended maximum of {MAX_BLOCK_DURATION_MIN} min. "
		f"Ensure balance between challenge & exhaustion."
		)
		warnings.warn(warning_msg)

	# Print update on the duration of the experiment, blocks and trials.
	print(
	f"\nExperiment duration: {exp_dur_min:.2f} min."
	f"\nAverage block duration: {block_dur_min:.2f} min."
	f"\nAverage trial duration: {trial_dur_sec:.2f} sec."
	)

	# Ensure that duration of all trials is positive
	invalid_trials = [{"trial" : i, "duration": d} for i, d in enumerate(trial_durs) if d<= 0]
	if invalid_trials:
		raise ValueError(
			"Verify input parametes. Invalid trial durations found."
			f"\n{invalid_trials}."
			)
	
	# 07. SAVE TRIALS -----------------------------------------------------------------------------
	# Create a dataframe from the list of dictionaries
	df = pd.DataFrame(BLOCK_COMBOS)

	# Initialize a column for the difference between the standard and deviant frequency
	df['freq_diff'] = [[None] for _ in range(len(df))]
	df['freq_diff_abs'] = [[None] for _ in range(len(df))]

	# Add the difference, if applicable
	for row, series in df.iterrows():
		f_diff = []
		f_diff_abs = []
		std_freq = series.base_freq

		if series.freq_dev:
			for i in series.freq_dev:
				if i:
					diff_abs = np.abs(std_freq - i)
					f_diff_abs.append(int(diff_abs))

					if i > std_freq: # higher devs
						diff = diff_abs
					else: # lower devs
						diff = -diff_abs
					f_diff.append(int(diff))
	
		df.at[row, 'freq_diff'] = f_diff if f_diff else [False]
		df.at[row, 'freq_diff_abs'] = f_diff_abs if f_diff_abs else [False]

	# Save the dataframe as a .csv file
	filename =  f"ses-{sesID:003d}_exp_parameter_combo.csv"
	out_path = Path(params["OUT_PATH"])
	out_path.mkdir(exist_ok=True, parents=True)
	out_dir  = out_path / filename

	if save_csv:
		df.to_csv(out_dir, sep=",", index=False)
		print(f"\nSaved {filename} to {out_path}.")	

# 02. EXAMPLE USAGE & SIMULATION OF EXPERIMENTAL SESSIONS -----------------------------------------
if __name__ == "__main__":
	freq_int = [192, 220, 392, 440] # G3, A3, G4, A4
	params = {
	
	"OUT_PATH" : "/home/mutrosa/Documents/projects/auditory_paradigms/detection_accuracy/trials",

	# a. Overall structure of the experimental session
	"NO_BLOCKS" : 4, 	    # Number of blocks, equal to the number of funcional scans in the MRI protocol
	"ITI_MIN"   : 2000,     # Must be noticeably larger than max(ISI) + tone_duration
	"ITI_MAX"   : 2500,     # Smaller than inter-block-interval (max rest time = 2 min)
	
	# b. Tone sequence
	"TONE_DURATION" : 100,   # Duration of a single tone in msec

	# If kept constant, the length of tone sequences is the same for each experimental session.
	# If not, length of tone sequence is chosen randomly from the range and kept constant across sesions.
	"MIN_TONES" : 7,    # Min. no. of tones in a single sequence
	"MAX_TONES" : 7,    # Max. no. of tones in a single sequence

	# c. Inter Stimulus Interval is the time between presentation of two sequential tones.
	"ISI_MIN"  : 700,        # Min. duration of ISI 
	"ISI_MAX"  : 700,        # Max. duration of ISI
	"ISI_STEP" : 300,    	 # Step size of the ISI range (population) TODO: this may be obsolete for MRI (not for beh)
	
	# d. Timing deviants
	"DEVS"    : [0, 4, 8, 13, 19, 27, 36, 48, 63, 80, 100, 125], # Absolute timing deviants in msec
	"DEV_REP" : 4,	# How many times should each deviation repeat across the exp. session?

	"FIRST_DEV_LOC" : 4,  # The first tone that can be displaced:
						  # e.g.: if you want the first few tones to be timing standards
	"LAST_DEV_LOC"  : 6,  # The last tone to be displaced timing-wise

	# c. Frequency deviants
	"FREQS" : freq_int,   # Absolute frequency deviants in Hz
	"FREQ_REP_MAX"   : 3, # How many times max can frequency deviations occur per trial?
						  # If 3, it means there could be 0, 1, 2, or 3 deviants in one trial
						  # That's good, because we have 4 buttons in the MRI
  
	"FIRST_FREQ_LOC" : 2,  # The first tone that can be displaced frequency-wise
						   # Easier to count if the first 2 tones are frequency standards

	"LAST_FREQ_LOC"  : 7,  # The last tone to be displaced frequency-wise
	}

	for session in range(1, 10):
		with open(f"trials/ses-{session:003d}_exp_parameter_combo.txt", "w") as f:
			sys.stdout = f
			create_experimental_sessions(params, session, save_csv=True)