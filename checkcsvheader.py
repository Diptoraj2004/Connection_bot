# check_csv_headers.py
import os, csv
from config import DATASET_PATH  # uses your configured dataset path

def check_csv_headers(folder=DATASET_PATH):
    headers_dict = {}
    if not os.path.exists(folder):
        print(f"❌ Dataset folder not found: {folder}")
        return headers_dict

    for f in os.listdir(folder):
        if f.endswith(".csv"):
            path = os.path.join(folder, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    reader = csv.reader(fh)
                    headers = next(reader, [])
                    headers_dict[f] = headers
            except Exception as e:
                headers_dict[f] = [f"⚠️ Error: {e}"]
    return headers_dict


if __name__ == "__main__":
    headers = check_csv_headers()
    for file, cols in headers.items():
        print(f"\n📂 {file}:")
        print("   ", cols)
