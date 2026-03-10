#! /usr/bin/env python
# Time-stamp: <2024-14-04 m.utrosa@bcbl.eu>
from expyriment import stimuli, design

class OddTone(stimuli.Tone): # Inheriting expyriment's class Tone. Adding stamp to see if the tone is a standard or deviant.
    def __init__(self, duration, frequency=None, samplerate=None, bitdepth=None, amplitude=None, category="standard"):
        super().__init__(duration, frequency=None, samplerate=None, bitdepth=None, amplitude=None)
        self.category = category # Is the tone a standard or a deviant?
        self.standard_frequency = frequency

class Devil():
    def __init__(self, magnitude, direction, location): 
        self.magnitude = magnitude # How big of a devil is it in msec?
        self.direction = direction # Prolonging or Shortening or Haciendo Nada with the ISI: late, early, on-time.
        self.location  = location  # To which sequential ISI in the sequence does the devil apply?
        # self.frequency = frequency  # How many devils do we have per sequence?
        
    def __str__(self):
        return f"The timing of tone no. {self.location + 1} is {self.direction} by {self.magnitude} msec."

class ToneSequence():
    
    def __init__(self, isi, tone, no_tones):
        self.isi  = isi
        self.tone = tone
        self.no_tones = no_tones
        
    def __str__(self):
        return f"A tone sequence with {self.isi}-msec-long inter-stimulus-intervals and {self.no_tones} tones in total."
    
    def create_sequence(self, devil=False):
        """
        Creates a list of [stimulus, ISI, stimulus, ISI, stimulus, ...]
        Sequence starts with the onset of the first tone.
        Sequence ends with the offset of the last tone (no ISI after the last tone).
        """
        sequence = []
        
        for t in range(self.no_tones):

            # ----- ADD TONE ----- 
            sequence.append(self.tone)
            
            # ----- ADD ISI ----- 
            if t < self.no_tones + 1:
                current_isi = self.isi
                
                if devil and devil.location == (i + 1):                
                    if devil.direction == "early":
                        current_isi -= devil.magnitude

                    elif devil.direction == "late":
                        current_isi += devil.magnitude

            sequence.append(current_isi)
            
        return sequence

class OddTrial(design.Trial): # Extended and customized by inheriting expyiriment's class Trial.
    
    def __init__(self, seq_number, InterSeqInterval, stimulus):
        super().__init__()
        self.seq_number = seq_number
        self.InterSeqInterval = InterSeqInterval
        self.stimulus = stimulus
        
    def __str__(self):
        return f"The trial has {self.seq_number} stimuli, each separated by {self.InterSeqInterval}. Stimulus is: {self.stimulus}"
    
    def create(self):
        
        stimuli_per_trial = []
        c = 0
        for _ in range(self.seq_number):
            stimuli_per_trial.append(self.stimulus)
            c += 1
            if c < self.seq_number:
                stimuli_per_trial.append(self.InterSeqInterval)
        
        return stimuli_per_trial

class OddBlock(design.Block): # Extended and customized by inheriting expyiriment's class Block.
    
    def __init__(self, name=None, trial_number, iti, trial):
        super.__init__(name=None)
        self.trial_number = trial_number
        self.iti = iti
        self.trial = trial
        
    def __str__(self):
        return f"The block has {self.trial_number} trials, each separated by {self.iti} msec."
    
    def create(self):
        stimuli_per_block = []
        c = 0
        for _ in range(self.trial_number):
            stimuli_per_block.append(self.trial)
            c += 1
            
            if c < self.trial_number:
                stimuli_per_block.append(self.iti)
        
        return stimuli_per_block
