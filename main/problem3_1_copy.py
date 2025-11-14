import pandas as pd
import numpy as np
import os

# Đọc dữ liệu với xử lý lỗi
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "results.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = pd.read_csv(input_path)
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

# Chọn các cột chỉ chứa dữ liệu số (các cột chỉ số cần phải tính)
number_attributes = data.select_dtypes(include=[float, int]).columns

# Khởi tạo từ điển kết quả với cột "Team"
results = {"Team": ["all"]}

# Tính trung vị, trung bình và độ lệch chuẩn cho từng chỉ số cho cả giải đấu
for x in number_attributes:
    results[f"Median of {x}"] = [f"{data[x].median(skipna=True):.2f}"]
    results[f"Mean of {x}"] = [f"{data[x].mean(skipna=True):.2f}"]
    results[f"Std of {x}"] = [f"{data[x].std(skipna=True):.2f}"]

# Nhóm dữ liệu theo từng đội bóng và tính trung vị, trung bình, độ lệch chuẩn cho từng đội
for team, group in data.groupby('Team'):
    results["Team"].append(team)
    for x in number_attributes:
        results[f"Median of {x}"].append(f"{group[x].median(skipna=True):.2f}")
        results[f"Mean of {x}"].append(f"{group[x].mean(skipna=True):.2f}")
        results[f"Std of {x}"].append(f"{group[x].std(skipna=True):.2f}")

# Chuyển kết quả thành DataFrame
results_df = pd.DataFrame(results)

# Lưu kết quả vào file 'results2.csv'
results_df.to_csv("results2.csv", index=False)