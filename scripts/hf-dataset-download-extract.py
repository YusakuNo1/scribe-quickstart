import argparse
import pandas as pd
import os
import wave
import io
from huggingface_hub import snapshot_download

def trim_audio(audio_bytes, start_sec=0.0, end_sec=None):
    """Trim WAV audio bytes to [start_sec, end_sec]. Returns original bytes if not WAV."""
    try:
        with wave.open(io.BytesIO(audio_bytes)) as r:
            framerate = r.getframerate()
            n_channels = r.getnchannels()
            sampwidth = r.getsampwidth()
            total_frames = r.getnframes()

            start_frame = int(start_sec * framerate)
            end_frame = int(end_sec * framerate) if end_sec is not None else total_frames
            end_frame = min(end_frame, total_frames)

            r.setpos(start_frame)
            frames = r.readframes(end_frame - start_frame)

        buf = io.BytesIO()
        with wave.open(buf, mode='wb') as w:
            w.setnchannels(n_channels)
            w.setsampwidth(sampwidth)
            w.setframerate(framerate)
            w.writeframes(frames)
        return buf.getvalue()
    except Exception:
        # Not a standard WAV; return as-is
        return audio_bytes


def get_audio_duration(audio_bytes):
    """Get audio duration in seconds by reading the binary stream."""
    try:
        with wave.open(io.BytesIO(audio_bytes)) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return round(duration, ndigits=4)
    except Exception:
        # Not a standard WAV format; return None
        return None

def extract_hf_dataset(repo_id, audio_column='audio', split='test', start_time=0.0, end_time=None):
    # 1. Download raw Parquet files
    print(f"Downloading files from {repo_id}...")
    local_repo_path = snapshot_download(
        repo_id=repo_id, 
        repo_type="dataset",
        allow_patterns=f"*/{split}-*.parquet"
    )

    parquet_files = [
        os.path.join(dp, f) for dp, dn, filenames in os.walk(local_repo_path) 
        for f in filenames if f.endswith(".parquet")
    ]

    if not parquet_files:
        print(f"No parquet files found for split: {split}")
        return

    # Prepare output directories
    dataset_name = repo_id.split('/')[-1]
    output_dir = f"{dataset_name}_{split}_extracted"
    audio_dir = os.path.join(output_dir, 'audio')
    
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    all_rows = []
    global_index = 0

    for parquet_file in parquet_files:
        print(f"Processing: {os.path.basename(parquet_file)}")
        
        # Read raw data with pandas
        df = pd.read_parquet(parquet_file)
        
        for _, row in df.iterrows():
            audio_entry = row[audio_column]
            
            audio_bytes = None
            if isinstance(audio_entry, dict) and 'bytes' in audio_entry:
                audio_bytes = audio_entry['bytes']
            elif isinstance(audio_entry, bytes):
                audio_bytes = audio_entry
            
            if audio_bytes is not None:
                audio_bytes = trim_audio(audio_bytes, start_sec=start_time, end_sec=end_time)

                # Get duration
                duration = get_audio_duration(audio_bytes)

                # Save audio file; append trim range to filename if clipped
                trimmed = start_time > 0.0 or end_time is not None
                trim_tag = f"_trim_{start_time}s-{end_time if end_time is not None else 'end'}s" if trimmed else ""
                file_name = f"audio_{global_index}{trim_tag}.wav"
                file_path = os.path.join(audio_dir, file_name)

                with open(file_path, mode='wb') as f:
                    f.write(audio_bytes)
                
                # Build CSV row: drop the raw audio column and convert to dict
                meta_dict = row.drop(audio_column).to_dict()
                
                # Clean numpy types and append new fields
                clean_row = meta_row_cleaner(meta_dict)
                clean_row['audio_file'] = os.path.join('audio', file_name)
                clean_row['duration_seconds'] = duration
                
                all_rows.append(clean_row)
                global_index += 1

    # 2. Save results to CSV
    if all_rows:
        metadata_df = pd.DataFrame(all_rows)
        metadata_csv_path = os.path.join(output_dir, 'metadata.csv')
        
        # utf-8-sig so Excel opens without garbled text
        metadata_df.to_csv(path_or_buf=metadata_csv_path, index=False, encoding='utf-8-sig')
        
        print(f"\nSuccessfully extracted {global_index} records.")
        print(f"Audio files: {os.path.abspath(audio_dir)}")
        print(f"Metadata CSV: {os.path.abspath(metadata_csv_path)}")
    else:
        print("No audio records were extracted.")

def meta_row_cleaner(d):
    """Coerce data types for CSV export compatibility."""
    clean_dict = {}
    for k, v in d.items():
        # Skip binary columns
        if isinstance(v, (bytes, bytearray)):
            continue
        # Unwrap numpy/pandas scalar types (ndim == 0 guards against multi-element arrays)
        if hasattr(v, 'item') and callable(v.item) and getattr(v, 'ndim', -1) == 0:
            clean_dict[k] = v.item()
        else:
            clean_dict[k] = v
    return clean_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='hf-dataset-download-extract')
    parser.add_argument('--repo-id', required=True, help='HuggingFace dataset repo ID (e.g. owner/repo)')
    parser.add_argument('--split', default='test', help='Dataset split to extract (default: test)')
    parser.add_argument('--start-time', type=float, default=0.0, help='Trim start time in seconds (default: 0)')
    parser.add_argument('--end-time', type=float, default=None, help='Trim end time in seconds (default: end of audio)')
    args = parser.parse_args()

    extract_hf_dataset(repo_id=args.repo_id, split=args.split, start_time=args.start_time, end_time=args.end_time)
