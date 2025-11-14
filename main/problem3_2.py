import pandas as pd
import numpy as np
import os

# Đọc dữ liệu với xử lý lỗi
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "results.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    print(f"Successfully loaded data from {input_path}")
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit(1)
except pd.errors.EmptyDataError:
    print("Error: The CSV file is empty")
    exit(1)
except pd.errors.ParserError:
    print("Error: Failed to parse the CSV file")
    exit(1)
except Exception as e:
    print(f"Unexpected error while reading file: {e}")
    exit(1)

df.fillna({
    'Standard_Gls': 0,
    'Standard_Ast': 0,
    'Standard_xG': 0,
    'Standard_xAG': 0,
    'Passing_Cmp': 0,
    'Defense_Tkl': 0,
    'Possession_Touches': 0,
    'Standard_Min': 0,
    'Standard_MP': 0,
    'Standard_Starts': 0,
    'Standard_90s': 0,
    'Shooting_SoT%': 'N/A',
    'Shooting_SoT': 'N/A',
    'Passing_Att': 'N/A',
    'Passing_Cmp%': 'N/A',
    'Defense_Int': 'N/A',
    'Defense_Blocks': 'N/A',
    'Possession_Prog': 'N/A',
    'Playing_Time_90s': 'N/A'
}, inplace=True)

for column in df.columns:
    if df[column].isna().any():
        if column not in ['Standard_Gls', 'Standard_Ast', 'Standard_xG', 'Standard_xAG',
                          'Passing_Cmp', 'Defense_Tkl', 'Possession_Touches',
                          'Standard_Min', 'Standard_MP', 'Standard_Starts', 'Standard_90s']:
            df[column].fillna('N/A', inplace=True)

# Hàm ước tính giá trị chuyển nhượng
def estimate_transfer_value(row):
    base_value = 0

    # Giá trị cơ bản theo vị trí
    if "FW" in row['Pos']:
        base_value = 15
    elif "MF" in row['Pos']:
        base_value = 10
    elif 'DF' in row['Pos']:
        base_value = 8
    elif 'GK' in row['Pos']:
        base_value = 5
    else:
        base_value = 5

    age_factor = max(0.5, 1.5 - (row['Age'] - 20) * 0.03)

    performance_factor = 1 + (
        row['Standard_Gls'] * 0.2 +
        row['Standard_Ast'] * 0.15 +
        row['Standard_xG'] * 0.1 +
        row['Standard_xAG'] * 0.1
    ) / 10

    return base_value * age_factor * performance_factor


df['Transfer_Value'] = df.apply(estimate_transfer_value, axis=1)

# Định dạng giá trị chuyển nhượng
df['Transfer_Value_Str'] = df['Transfer_Value'].apply(lambda x: f"EUR {x:.1f}M")

print(df[['Player', 'Team', 'Pos', 'Age', 'Standard_Gls', 'Standard_Ast', 'Transfer_Value']]
      .sort_values('Transfer_Value', ascending=False)
      .head(20))

#Lưu File:
columns_to_save = ['Player', 'Team', 'Pos', 'Age', 'Standard_Gls', 'Standard_Ast', 'Standard_xG', 'Standard_xAG', 'Transfer_Value', 'Transfer_Value_Str']
df[columns_to_save].to_csv("results3_2.csv", index=False)