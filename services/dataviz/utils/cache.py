import os, time
import pandas as pd

def load_or_fetch(cache_path, fetch_func, *args, **kwargs):
    if os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < 3600 * 24:
            return pd.read_csv(cache_path)
    df = fetch_func(*args, **kwargs)
    df.to_csv(cache_path, index=False)
    return df
