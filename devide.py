import pandas as pd
import os

# --------------------------------------------------
# INPUT CSV
# --------------------------------------------------
INPUT_CSV = "csv_bdw.csv"

# --------------------------------------------------
# OUTPUT FOLDER
# --------------------------------------------------
OUTPUT_DIR = "csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# LOAD CSV
# --------------------------------------------------
df = pd.read_csv(INPUT_CSV)

# --------------------------------------------------
# SHUFFLE ROWS RANDOMLY
# --------------------------------------------------
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# --------------------------------------------------
# SPLIT INTO 3 PARTS
# --------------------------------------------------
n = len(df)

part1_end = n // 3
part2_end = 2 * n // 3

df_r1 = df.iloc[:part1_end]
df_r2 = df.iloc[part1_end:part2_end]
df_r3 = df.iloc[part2_end:]

# --------------------------------------------------
# SAVE CSV FILES
# --------------------------------------------------
csv_r1 = os.path.join(OUTPUT_DIR, "CSV_R1.csv")
csv_r2 = os.path.join(OUTPUT_DIR, "CSV_R2.csv")
csv_r3 = os.path.join(OUTPUT_DIR, "CSV_R3.csv")

df_r1.to_csv(csv_r1, index=False)
df_r2.to_csv(csv_r2, index=False)
df_r3.to_csv(csv_r3, index=False)

# --------------------------------------------------
# REPORT
# --------------------------------------------------
print("\nCSV Split Completed Successfully")
print("-" * 40)
print(f"Total Rows : {n}")
print(f"CSV_R1     : {len(df_r1)} rows")
print(f"CSV_R2     : {len(df_r2)} rows")
print(f"CSV_R3     : {len(df_r3)} rows")
print("-" * 40)
print(f"Saved to: {OUTPUT_DIR}")