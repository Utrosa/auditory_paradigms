#! /usr/bin/env python
# Time-stamp: <02-10-2025>
# Created by Sofia Tagliani on 25.09.2025
# Proof-read by Monika on XX.XX.XXXX
# Calculating sensitivity (d') from the timing_dev_task.py

import pandas as pd
import numpy as np
from scipy.stats import norm

#Load data: note it was importing as single column so I specified sep is commas, and to ignore the first line starting with #
data = pd.read_csv("sub-01_ses-01_task-Timing_dev_ts-1758630737.tsv",  sep=",",comment="#" ) # change to your actual filename

#Files used: relative file paths used for the diff participants-- paste above. 
#Sofia: sub-04_ses-05_task-Timing_dev_ts-1758633988.tsv
#Monika: sub-01_ses-01_task-Timing_dev_ts-1758630737.tsv

# Conditions:
hits = ((data["DELTA"] != 0) & (data["RESPONSE"].notna())).sum()
misses = ((data["DELTA"] != 0) & (data["RESPONSE"].isna())).sum()
correct_rejections = ((data["DELTA"] == 0) & (data["RESPONSE"].isna())).sum()
false_alarms = ((data["DELTA"] == 0) & (data["RESPONSE"].notna())).sum()

# Calculate different rates 
hit_rate = hits / (hits + misses) 
fa_rate = false_alarms / (false_alarms + correct_rejections)

# Corrction of extreme values cause I was getting -infinity for z scores (since false alarm rate was 0 for both me and Monika)
# I did this based on this discussion https://stats.stackexchange.com/questions/134779/d-prime-with-100-hit-rate-probability-and-0-false-alarm-probability
if hit_rate == 1:
    hit_rate = 1 - (1 / (2 * (hits + misses)))
elif hit_rate == 0:
    hit_rate = 1 / (2 * (hits + misses))

#This was the one actually causing problems, but I added the same correction above just in case
if fa_rate == 1:
    fa_rate = 1 - (1 / (2 * (false_alarms + correct_rejections)))
elif fa_rate == 0:
    fa_rate = 1 / (2 * (false_alarms + correct_rejections))

# Calculate z scores 
z_hit = norm.ppf(hit_rate)
z_fa = norm.ppf(fa_rate)

# Calculate d' (sensitivity index)
d_prime = z_hit - z_fa

# Print results (I added formatting to 3 decimal places for the rates and d')
print(f"Hits: {hits}")
print(f"Misses: {misses}")
print(f"Correct Rejections: {correct_rejections}")
print(f"False Alarms: {false_alarms}")
print(f"Hit Rate: {hit_rate:.3f}")
print(f"False Alarm Rate: {fa_rate:.3f}")
print(f"Z(Hit Rate): {z_hit:.3f}")
print(f"Z(False Alarm Rate): {z_fa:.3f}")
print(f"d′: {d_prime:.3f}")

#Example output: me 
# Hits: 253
# Misses: 124
# Correct Rejections: 7
# False Alarms: 0
# Hit Rate: 0.671
# False Alarm Rate: 0.071
# Z(Hit Rate): 0.443
# Z(False Alarm Rate): -1.465
# d′: 1.908


#Example output: Monika
# Hits: 129
# Misses: 248
# Correct Rejections: 7
# False Alarms: 0
# Hit Rate: 0.342
# False Alarm Rate: 0.071
# Z(Hit Rate): -0.407
# Z(False Alarm Rate): -1.465
# d′: 1.059