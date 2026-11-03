We designed several tasks using [Expyriment](https://expyriment.org/), a Python library for programming experiments in cognitive science, to study the prediction error responses to tone frequency and tone timing deviants in human participants. All tasks are coded in Python and can be used in cognitive neuroscience research, ensuring high-degree of precision, customization, and ease of use.

## Functional Localizer - fMRI
An implementation of a functional localizer task that activates the auditory brain areas during MRI scanning. Participants are presented with natural sounds interspersed with silent periods and are asked to determine whether each sound has been repeated or not by pressing a button.

## A. Timing Deviance Detection - Behavioral - Psychophysics
The task consists of sequentially presenting multiple tone sequences. The timing of at least one of the tones in each sequence is randomly altered and the participants are asked to press a key when they hear this displacement. The displaced tone can occur too early (shorter ISI), too late (longer ISI), or on-time in reference to previously heard timing standards. The timing of the first three tones of the sequence is kept constant. The goal is to determine participants' individual accuracy in detecting timing deviants. The instruction is to detect timing deviants.

## B. Frequency Deviance Detection - fMRI
This is a classic auditory oddball paradigm in which the oddballs are deviants either in tone timing or tone frequency. The timing deviants occur once per sequence whereas the frequency deviants are more frequent (this can be adapted easily). The instruction is to count frequency deviants and report the count via a button press. The's implementation is adapted for neuroimaging experiments: waiting for starting triggers from the MRI and other protocol-related peculiarities.

## C. Color Change Detection - fMRI
This is similar to *B. Frequency Deviance Detection* with a different instruction for the participant. Instead of counting frequency deviants, the attention is put to the fixation cross, and the count is related to the amount of time it changes color.
Other key adaptations:
- continuous stream of tones per run instead of tone sequences
- balanced representation of timing and frequency events