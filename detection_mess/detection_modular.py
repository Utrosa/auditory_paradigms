#! /usr/bin/env python
# Time-stamp: <2024-14-04 m.utrosa@bcbl.eu>

# CLASSESS
class OddTone(stimuli.Tone): # Inheriting expyriment's class Tone. Adding stamp to see if the tone is a standard or deviant.

    def __init__(self, duration, frequency=None, samplerate=None, bitdepth=None, amplitude=None, category)
        super.__init__(duration, frequency=None, samplerate=None, bitdepth=None, amplitude=None)
        self.category() = category # Is the tone a standard or a deviant?

class Devil():
    
    def __init__(self, magnitude, direction, location): 
        self.magnitude = magnitude # How big of a devil is it in msec?
        self.direction = direction # Prolonging or Shortening or Haciendo Nada with the ISI: late, early, on-time.
        self.location  = location  # To which sequential ISI in the sequence does the devil apply?
        # self.frequency = frequency  # How many devils do we have per sequence?
        
    def __str__(self):
        return f"Timing of tone no. {self.location + 1} is {self.direction} by {self.magnitude} msec."

class Sequence():
    
    def __init__(self, isi, tone, no_tones):
        self.isi  = isi
        self.tone = tone
        self.no_tones = no_tones
        
    def __str__(self):
        return f"A sequence with {self.isi}-msec-long inter-stimulus-intervals and {self.no_tones} tones in total."
    
    def create_noDev(self):
        tones_per_seq = []
        
        # Sequence starts with the onset of the first tone and ends with the offset of the last tone.
        c = 0
        for _ in range(self.no_tones):
            tones_per_seq.append(self.tone)
            c += 1
            
            if c < self.no_tones:
                tones_per_seq.append(self.isi)
        
        return tones_per_seq
    
    def create_withDev(self, devil):
        tones_per_seq = []        
        c = 0
        for _ in range(self.no_tones):
            tones_per_seq.append(self.tone)
            c += 1
            
            if c < self.no_tones: # Start with 1st tone's onset and end with the last's tone offset.
                
                if devil.location == c:
                    if devil.direction == "early":
                        isi_early = self.isi - devil.magnitude
                        tones_per_seq.append(isi_early)

                    elif devil.direction == "late":
                        isi_late = self.isi + devil.magnitude
                        tones_per_seq.append(isi_late)
                else:
                    tones_per_seq.append(self.isi)
        
        return tones_per_seq

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
