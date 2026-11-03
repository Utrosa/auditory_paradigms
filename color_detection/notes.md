# PARAMETERS
## 01. Experiment's structure


## 02. Stimuli

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