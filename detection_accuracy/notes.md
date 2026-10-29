# PARAMETERS
## 01. Experiment's structure
- number of blocks/runs
- inter trial interval (ITI)

Number of trials is defined by the magnitudes, types and locations of
timing deviants.

## 02. Stimuli
- tone duration
- tone sequence length (number of tones per stimulus)
	NO_TONES is kept constant across all trials in a single exp. session. It can be randomly selected given the min & max values (variation across sessions) but if min & max are the same, NO_TONES is kept constant for all exp. sessions.
- inter stimulus interval (the beat)
	ISI is kept constant across all trials in a single exp. session. It can be randomly selected given the min & max values (variation across sessions) but if min & max are the same, ISI is kept constant for all exp. sessions.

## 03. Independent variable: Timing deviancy
- timing deviants
- timing deviant location in the stimulus (tone idx)
- timing deviant type (standard, early, or late)

## 04. Control variables: Frequency deviancy
- frequency deviants
- frequency deviant location in the stimulus (tone idx)
- frequency deviant repetition in the trial (rep idx)
- frequency deviant type (standard, higher, or lower)

## 05. Variables to save
- difference between standard and deviant for timing deviants
- difference between standard and deviant for frequency deviants

The choice of parameters is guided by simulating experimental session and chosing the ones where the distribution of frequency and timing deviants does not show any obvious patterns or correlations, to ensure no confounding effects.

# MRI
### VARY ACROSS TRIALS & EXP. SESSIONS
ITI is randomly sampled in len(no_trials) on each experimental session.

### CONSTANT OVER TRIALS & VARY ACROSS EXP. SESSIONS
ISI if min & max are NOT the same value in params
NO_TONES if min & max are NOT the same value in params

### CONSTANT OVER TRIALS & CONSTANT ACROSS EXP. SESSIONS
ISI if min & max are the same value in params
NO_TONES if min & max are the same value in params

# BEHAVIORAL
### VARY ACROSS TRIALS & EXP. SESSIONS

### CONSTANT OVER TRIALS & VARY ACROSS EXP. SESSIONS

### CONSTANT OVER TRIALS & CONSTANT ACROSS EXP. SESSIONS

### MIGHT BE A RELEVANT CHECK FOR BEH. EXP.
	# To ensure block separability, a change in ISI should 
	# not be perceived as a deviation (change in tempo)
	if len(ISI) > 1:
		if params["ISI_STEP"] < 2 * max(DEV):
			raise ValueError(
				f'The step ({params["ISI_STEP"]} ms) between ISI values '
				f'{ISI} could be too small given the max deviation ({max(DEV)} ms).'
				)