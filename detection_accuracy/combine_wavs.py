import os
import re
import numpy as np
from scipy.io.wavfile import read, write

#### EURIA'S CODE: check check needed
def parse_filename(filename):
    """
    Extracts run, trial, type, and sequence index from the filename.
    Returns a dict or None if parsing fails.
    """
    # Pattern explanation:
    # (tone|isi|iti) : Capture the type
    # -(\d+)         : Capture the sequence index (the number immediately after type)
    # .*?            : Non-greedy match for any intermediate text (like _len-700)
    # _trial-(\d+)   : Capture the trial number
    # _run-(\d+)     : Capture the run number
    pattern = r"(tone|isi|iti)-(\d+).*?_trial-(\d+)_run-(\d+)\.wav$"
    
    match = re.search(pattern, filename, re.IGNORECASE)
    
    if match:
        return {
            "filename": filename,
            "type": match.group(1).lower(),
            "seq_idx": int(match.group(2)), # The number after tone/isi/iti
            "trial": int(match.group(3)),
            "run": int(match.group(4))
        }
    return None

def combine_wav_files_per_run_trial(folder_path, output_folder=None):
    """
    Scans a folder for WAV files, groups them by run and trial, 
    sorts them by sequence index first, then by type (tone -> isi),
    to create an alternating tone-isi-tone-isi sequence.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    if output_folder is None:
        output_folder = folder_path
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Collect and parse all valid WAV files
    files_data = []
    for f in os.listdir(folder_path):
        if f.lower().endswith('.wav'):
            parsed = parse_filename(f)
            if parsed:
                parsed["path"] = os.path.join(folder_path, f)
                files_data.append(parsed)
            else:
                print(f"Skipping file (name format not recognized): {f}")

    if not files_data:
        print("No valid files found matching the pattern.")
        return

    # 2. Group files by (run, trial)
    groups = {}
    for item in files_data:
        key = (item["run"], item["trial"])
        if key not in groups:
            groups[key] = []
        groups[key].append(item)

    print(f"Found {len(groups)} unique run/trial combinations to process.")

    # 3. Process each group
    for (run_idx, trial_idx), group_files in groups.items():
        
        # Define sort order for type: tone=0, isi=1, iti=2
        # This ensures that if seq_idx is the same (e.g., tone-1 and isi-1), 
        # 'tone' comes before 'isi'.
        type_order = {"tone": 0, "isi": 1, "iti": 2}
        
        # CORRECTED SORT LOGIC:
        # Primary Key: seq_idx (The step number: 1, 2, 3...)
        # Secondary Key: type (Ensures tone comes before isi for the same step)
        # Result: tone-1, isi-1, tone-2, isi-2, ...
        group_files.sort(key=lambda x: (x["seq_idx"], type_order.get(x["type"], 99)))
        
        file_paths = [item["path"] for item in group_files]
        
        # Define output filename
        output_filename = os.path.join(output_folder, f"combined_run-{run_idx:02d}_trial-{trial_idx:02d}.wav")
        
        # Call the combination logic
        combine_audio_list(file_paths, output_filename)

def combine_audio_list(file_paths, output_filename):
    """
    Internal helper to combine a specific list of files into one output.
    (Adapted from your provided snippet)
    """
    if not file_paths:
        return

    audio_data_list = []
    sample_rate = None

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}")
            continue
            
        try:
            rate, data = read(file_path)
            
            if sample_rate is None:
                sample_rate = rate
            elif rate != sample_rate:
                print(f"Warning: Sample rate mismatch in {os.path.basename(file_path)}. Using first file's rate ({sample_rate}).")
                # Proceeding with mismatch might cause speed issues, but we continue as per original logic
            
            # Normalize dtype to int16
            if data.dtype != np.int16:
                if np.issubdtype(data.dtype, np.floating):
                    # Scale float to int16 range
                    data = (data * 32767).astype(np.int16)
                else:
                    data = data.astype(np.int16)
            
            # Convert stereo to mono
            if len(data.shape) > 1 and data.shape[1] > 1:
                data = data.mean(axis=1).astype(np.int16)
            
            audio_data_list.append(data)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    if not audio_data_list:
        print(f"No valid audio data to combine for {output_filename}.")
        return

    combined_audio = np.concatenate(audio_data_list)
    write(output_filename, sample_rate, combined_audio)
    print(f"Created: {os.path.basename(output_filename)} ({len(audio_data_list)} segments)")

# --- Usage Example ---
AUDIO_FOLDER = "/home/mutrosa/Documents/projects/auditory_paradigms/detection_accuracy/stimuli_segments/"
combine_wav_files_per_run_trial(AUDIO_FOLDER)