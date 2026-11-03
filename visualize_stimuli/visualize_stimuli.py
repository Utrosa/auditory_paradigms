#! /usr/bin/env python
# Time-stamp: <23-06-2026, m.utrosa@bcbl.eu>
'''
To visualize .wav sound files.
Useful for presentations.

conda activate expyriment
'''
import random
import numpy as np
import librosa
import librosa.display
import matplotlib as mpl
from pathlib import Path
import matplotlib.pyplot as plt
task = "localizer" # "timDev" or "localizer"
if task == "timDev":
    y_setting = "hz"  # frequency range is determined by the FFT window and sampling rate.
elif task == "localizer":
    y_setting = "log" # the spectrum is displayed on a log scale.

# 00. Prerequisites -----------------------------------------------------------
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 14,
    "axes.titlesize": 14,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "axes.linewidth": 1.2,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "savefig.dpi": 300,
})

# 01. Get audio ---------------------------------------------------------------
outPath = Path(f"/home/mutrosa/Documents/projects/auditory_paradigms/stimuli/{task}")
AUDIO_FOLDER = outPath / "test" # stimuli

# Load wavs
audio_files = [
    f.name
    for f in AUDIO_FOLDER.glob("*.wav")
]
# Randomly select 5 sounds for the presentation
num_samples = min(4, len(audio_files))

selected_files = random.sample(audio_files, num_samples)
# selected_files = [
# "exp_combo-026_block_02_trial_06.wav",  # timDev only: -125 msec
# "exp_combo-026_block_02_trial_03.wav",  # freqDev only: -28Hz diff
# "exp_combo-026_block_01_trial_04.wav",  # silent trial
# "exp_combo-026_block_02_trial_08.wav",  # timDev and freqDev: +80 msec; +248 and +28 Hz diff
# "exp_combo-026_block_04_trial_04.wav",  # timDev and freqDev: -8 msec; +48Hz, -200Hz, -200Hz diff
# "exp_combo-026_block_01_trial_03.wav"   # no timDev and no freqDev

# ]

# 02. Spectrograms per sound --------------------------------------------------
cols = 2
rows = 2
fig, axes = plt.subplots(
    rows,
    cols,
    figsize = (10, 7),
    constrained_layout=True,
    sharex=True,
    sharey=True
)
axes = axes.flatten()
shortnames = []
all_audio = []
durations = []
sr = 48000

for i, file_name in enumerate(selected_files):

    # Extract a short name of the sound (for localizer sounds)
    if task == "localizer":

        # Removing all characters after "_ramp" and strip "s3_" from the start
        # s3_animal_1_ramp10.wav
        loc = file_name.find("_ramp")
        short_name = file_name[3:loc] # OJO: Adding "-3" to "loc" removes the IDX of the sound
        shortnames.append(short_name)

    elif task == "timDev":

        # Removing all characters after "_isi" and strip "sequence_" from the start
        # sequence_delta_4_isi_500.wav
        loc = file_name.find(".wav")
        short_name = file_name[4:loc]
        shortnames.append(short_name)

    
    # Load sounds
    file_path = AUDIO_FOLDER / file_name
    y, sr = librosa.load(file_path, sr=sr)

    # Combine into one stimulus
    all_audio.append(y)
    durations.append(len(y) / sr)

    # Short fourier transform per sound
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

    # Create an image per sounds
    img = librosa.display.specshow(
        S_db,
        sr=sr,
        x_axis="time",    # values are plotted in seconds
        y_axis=y_setting, # frequency type
        ax=axes[i]
    )
    if task == "timDev":
        axes[i].set_ylim(0, 5000)

        T_END = 5.0
        tone_dur = 0.050
        isi = 0.700

        n_tones = 7

        # tone onsets are explicitly defined
        onsets = np.arange(n_tones) * (tone_dur + isi)

        offsets = onsets + tone_dur
        axes[i].set_ylim(0, 5000)
        axes[i].set_xlim(0, 4.55)

        for on in onsets:
            axes[i].axvline(on, color="white", linestyle="--", linewidth=1)

    axes[i].set_title(short_name, fontsize=14, fontweight="bold", pad=6)
    axes[i].label_outer()
    axes[i].set_ylim(0, 8192)

# Add a shared colorbar and axis labels
cbar = fig.colorbar(
    img,
    shrink=0.9,
    pad=0.02,
    ax=axes,
    format="%+2.0f dB")

# Save and show
if task == "timDev":
    filename =  str(outPath / f"exp_combo-026_task-{task}_stimuli_examples_NOTITLE.png")
elif task == "localizer":
    filename = str(outPath / f"task-{task}_stimuli_examples.png")

fig.savefig(
    filename,   
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()

# 03. Spectrograms for a sound sequence ---------------------------------------
# Concatenate all audio signals into one
combined_audio = np.concatenate(all_audio)

# STFT for all sounds
S = librosa.stft(combined_audio)
S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

# Plot one spectrogram
fig, ax = plt.subplots(figsize=(18, 6))

img = librosa.display.specshow(
    S_db,
    sr=sr,
    x_axis="time",
    y_axis=y_setting,
    ax=ax
)

# Compute boundaries and centers (in seconds)
# boundaries = np.cumsum([0] + durations)
# centers = [(boundaries[i] + boundaries[i+1]) / 2 for i in range(len(durations))]
# ax.set_xticks(centers)
# ax.set_xticklabels(shortnames, rotation=45, ha="right", fontsize=12)
n = min(len(shortnames), len(durations))
shortnames = shortnames[:n]
durations = durations[:n]

boundaries = np.cumsum([0] + durations)
centers = [(boundaries[i] + boundaries[i+1]) / 2 for i in range(n)]

ax.set_xticks(centers)
ax.set_xticklabels(shortnames, rotation=45, ha="right", fontsize=12)

# Remove axis label (no seconds)
# ax.tick_params(axis='x', which='both', bottom=False, top=False)
# ax.set_xticks([])
# ax.set_xticklabels([])
# Vertical separator lines
# for b in boundaries:
#     ax.axvline(b, color="white", linewidth=1, alpha=0.8)
# ax.tick_params(axis='both', labelsize=12)
ax.set_ylabel("Hz", fontsize=14)
ax.set_ylim(0, 8192)

plt.colorbar(
    img,   
    shrink=0.9,
    pad=0.02,
    ax=ax,
    format="%+2.0f dB")
cbar.ax.tick_params(labelsize=12)
plt.tight_layout()


# Save and show
if task == "timDev":
    filename =  str(outPath / f"exp_combo-026_task-{task}_stimuli_examples_NOTITLE.png")
elif task == "localizer":
    filename = str(outPath / f"task-{task}_stimuli_examples_30-LABELS.png")

# fig.savefig(
#     filename,   
#     dpi=300,
#     bbox_inches="tight",
#     facecolor="white"
# )
# plt.show()