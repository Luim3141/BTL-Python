import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from datetime import datetime
import sys
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

# Chọn các cột số và xử lý dữ liệu
df_numeric = df.select_dtypes(include=[np.number])

# Ghi lại số lượng cột trước khi xử lý
original_columns = len(df_numeric.columns)
print(f"Original numeric columns: {original_columns}")

# Xóa các cột trống hoàn toàn
empty_cols = df_numeric.columns[df_numeric.isna().all()].tolist()
if empty_cols:
    print(f"Warning: Dropping completely empty columns: {empty_cols}")
    df_numeric.dropna(axis=1, how='all', inplace=True)

# Xử lý missing values – phiên bản FIX FutureWarning
if df_numeric.isna().any().any():
    print("Missing values found. Using median imputation...")

    missing_count = df_numeric.isna().sum().sum()
    print(f"Total missing values: {missing_count}")

    for column in df_numeric.columns:
        if df_numeric[column].isna().any():
            median_value = df_numeric[column].median()

            if pd.isna(median_value):
                median_value = 0
                print(f"Column '{column}': Using 0 (median was also NaN)")
            else:
                print(f"Column '{column}': Imputing with median {median_value:.3f}")

            # FIX: Không dùng inplace trên slice
            df_numeric[column] = df_numeric[column].fillna(median_value)

else:
    print("No missing values found.")

# Kiểm tra lại dữ liệu sau khi xử lý
print(f"Final numeric columns: {len(df_numeric.columns)}")
print(f"Data shape after processing: {df_numeric.shape}")

if df_numeric.empty:
    print("Error: No numeric data available after processing.")
    sys.exit(1)

# Xử lý infinite values
if np.isinf(df_numeric.values).any():
    print("Warning: Infinite values found. Replacing with 0...")
    df_numeric.replace([np.inf, -np.inf], 0, inplace=True)

# Chuẩn hóa dữ liệu
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_numeric)

inertia = []
silhouette_scores = []
K_range = range(2, 11)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    kmeans.fit(X_scaled)
    inertia.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))

# Vẽ biểu đồ Elbow & Silhouette
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.plot(K_range, inertia, marker='o')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(K_range, silhouette_scores, marker='o', color='orange')
plt.xlabel('Number of clusters (K)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score')
plt.grid(True)

plt.tight_layout()
elbow_silhouette_file = f"elbow_silhouette_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
plt.savefig(elbow_silhouette_file, dpi=300, bbox_inches='tight')
plt.close()

# Chọn số lượng nhóm tối ưu (giữ nguyên logic của bạn)
optimal_k = 4
print(f"Optimal number of clusters based on silhouette score: {optimal_k}")

# Phân cụm
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
clusters = kmeans.fit_predict(X_scaled)
df['Cluster'] = clusters

# PCA để trực quan hóa
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

cluster_names = {
    0: "Hậu vệ/Phòng ngự",
    1: "Tiền vệ trung tâm",
    2: "Tiền đạo/Tấn công",
    3: "Tiền vệ cánh/Công"
}

# Mapping tên nhóm
df['Tên Nhóm'] = df['Cluster'].map(cluster_names)

plt.figure(figsize=(12, 8))
sns.scatterplot(
    x=X_pca[:, 0],
    y=X_pca[:, 1],
    hue=df['Tên Nhóm'],
    palette='Set2',
    s=80
)

plt.title("Biểu đồ Phân cụm Cầu thủ (PCA - 2 chiều)", fontsize=16)
plt.xlabel("Thành phần chính 1")
plt.ylabel("Thành phần chính 2")
plt.legend(title='Nhóm Vị trí', loc='best')
plt.savefig("bieu_do_phan_cum_co_chu_thich.png", dpi=300)
