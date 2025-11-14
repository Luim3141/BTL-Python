import pandas as pd
import numpy as np
import os

# Đọc dữ liệu với xử lý lỗi
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "results2.csv")

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

# Danh sách các chỉ số để đánh giá
chi_so_quan_trong = [
    'Median of Standard_Gls', 'Mean of Standard_Gls',
    'Median of Standard_Ast', 'Mean of Standard_Ast',
    'Median of Standard_xG', 'Mean of Standard_xG',
    'Median of Standard_xAG', 'Mean of Standard_xAG',
    'Median of Passing_Cmp', 'Mean of Passing_Cmp',
    'Median of Possession_Touches', 'Mean of Possession_Touches',
    'Median of Defense_Int', 'Mean of Defense_Int',
    'Median of Goalkeeping_Save%', 'Mean of Goalkeeping_Save%'
]

# Tìm đội dẫn đầu cho từng chỉ số và lưu giá trị thống kê
doi_dan_dau = {}
gia_tri_cao_nhat = {}
for chi_so in chi_so_quan_trong:
    max_index = df[chi_so].idxmax()
    doi_tot_nhat = df.loc[max_index, 'Team']
    gia_tri = df.loc[max_index, chi_so]
    doi_dan_dau[chi_so] = doi_tot_nhat
    gia_tri_cao_nhat[chi_so] = gia_tri

# Đếm số lần mỗi đội dẫn đầu và lưu các chỉ số cụ thể
diem_so_doi = {}
chi_so_cua_doi = {}
for chi_so, doi in doi_dan_dau.items():
    if doi in diem_so_doi:
        diem_so_doi[doi] += 1
        chi_so_cua_doi[doi].append(chi_so)
    else:
        diem_so_doi[doi] = 1
        chi_so_cua_doi[doi] = [chi_so]

# Sắp xếp các đội theo điểm số
doi_xep_hang = sorted(diem_so_doi.items(), key=lambda x: x[1], reverse=True)

# Hiển thị kết quả chi tiết với giá trị thống kê
print(f"\n{'='*60}")
print("ĐỘI DẪN ĐẦU TỪNG CHỈ SỐ VÀ GIÁ TRỊ CỤ THỂ")
print(f"{'='*60}")
for chi_so, doi in doi_dan_dau.items():
    gia_tri = gia_tri_cao_nhat[chi_so]
    print(f"{chi_so}:")
    print(f"  Đội dẫn đầu: {doi}")
    print(f"  Giá trị: {gia_tri:.1f}")
    print()

print(f"\n{'='*60}")
print("BẢNG XẾP HẠNG ĐỘI DẪN ĐẦU THEO CHỈ SỐ")
print(f"{'='*60}")
for i, (doi, diem) in enumerate(doi_xep_hang, 1):
    print(f"{i}. {doi}: {diem} chỉ số")
    print(f"   Các chỉ số dẫn đầu:")
    for chi_so in chi_so_cua_doi[doi]:
        gia_tri = gia_tri_cao_nhat[chi_so]
        print(f"   - {chi_so}: {gia_tri:.1f}")
    print()