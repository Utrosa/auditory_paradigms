#### For presentation figures
import os
import random
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt

# 01. Get audio ---------------------------------------------------------------
AUDIO_FOLDER = "/home/mutrosa/Documents/projects/auditory_paradigms/localizer/stimuli"
audio_files = [
    f for f in os.listdir(AUDIO_FOLDER)
    if f.lower().endswith((".wav"))
]

# Random selection
num_samples    = min(30, len(audio_files))
selected_files = random.sample(audio_files, num_samples)

# 02. Spectrograms per sound --------------------------------------------------
fig, axes = plt.subplots(5, 6, figsize=(18, 12), constrained_layout=True)
axes = axes.flatten()

shortnames = []
all_audio = []
durations = []
sr = None

for i, file_name in enumerate(selected_files):

    # Extract a short name of the sound
    # Removing all characters after "_ramp" and strip "s3_" from the start
    loc = file_name.find("_ramp")
    short_name = file_name[3:loc]
    shortnames.append(short_name)
    
    # Load sounds
    file_path = os.path.join(AUDIO_FOLDER, file_name)
    y, sr = librosa.load(file_path, sr=None)

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
        x_axis="time",
        y_axis="log",
        ax=axes[i]
    )

    axes[i].set_title(short_name, fontsize=10)
    axes[i].label_outer()

# Add a shared colorbar
fig.colorbar(img, ax=axes, format="%+2.0f dB")
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
    y_axis="log",
    ax=ax
)

# Compute boundaries and centers (in seconds)
boundaries = np.cumsum([0] + durations)
centers = [(boundaries[i] + boundaries[i+1]) / 2 for i in range(len(durations))]
ax.set_xticks(centers)
ax.set_xticklabels(shortnames, rotation=45, ha="right")

# Remove axis label (no seconds)
ax.set_xlabel("")

# Vertical separator lines
# for b in boundaries:
#     ax.axvline(b, color="white", linewidth=1, alpha=0.8)

ax.set_ylabel("Frequency (Hz)")

plt.colorbar(img, ax=ax, format="%+2.0f dB")
plt.tight_layout()
plt.show()