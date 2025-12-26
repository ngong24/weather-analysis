
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from pathlib import Path
from datetime import datetime
import logging
from tqdm import tqdm
from scipy import stats
from statsmodels.graphics.tsaplots import plot_acf
from mpl_toolkits.mplot3d import Axes3D
import argparse

# Thiết lập cảnh báo
warnings.filterwarnings('ignore')

# Thiết lập style và font
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 150

def setup_logging():
  
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('visualization.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def create_output_directories(base_dir='weather_plots'):
    
    dirs = {
        'base': Path(base_dir),
        'correlation': Path(base_dir) / 'correlation_analysis',
        'timeseries': Path(base_dir) / 'time_series_analysis',
        'distribution': Path(base_dir) / 'distribution_analysis',
        'relationship': Path(base_dir) / 'relationship_analysis',
        'advanced': Path(base_dir) / 'advanced_analysis'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Đã tạo thư mục: {dir_path}")
    
    return dirs

def load_and_preprocess_data(filepath='weather_preprocessed.csv'):
    
    logger.info(f"Đang đọc dữ liệu từ {filepath}...")
    
    try:
        df = pd.read_csv(filepath)
        
        # Chuyển đổi cột time sang datetime
        df['time'] = pd.to_datetime(df['time'])
        
        # Tạo các biến đặc trưng từ thời gian
        df['month'] = df['time'].dt.month
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        df['day_of_year'] = df['time'].dt.dayofyear
        
        # Tạo biến mùa (1=Xuân, 2=Hạ, 3=Thu, 4=Đông)
        df['season'] = df['month'].apply(lambda x: 
            1 if x in [2, 3, 4] else 
            2 if x in [5, 6, 7] else 
            3 if x in [8, 9, 10] else 4
        )
        
        # Tạo biến trời mưa
        rain_cols = [col for col in df.columns if col in ['w_61', 'w_63', 'w_65']]
        if rain_cols:
            df['is_rainy'] = df[rain_cols].sum(axis=1) > 0
        else:
            df['is_rainy'] = False
        
        # Tạo biến ngày/đêm (6h-18h là ngày)
        df['is_day'] = df['hour'].between(6, 18)
        
        logger.info(f"Đã đọc thành công {len(df)} dòng dữ liệu")
        logger.info(f"Các cột: {df.columns.tolist()}")
        
        return df
        
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Lỗi khi đọc dữ liệu: {str(e)}")
        raise

def save_figure(fig, filepath, dpi=150):
   
    try:
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        logger.info(f"Đã lưu biểu đồ: {filepath}")
        plt.close(fig)
    except Exception as e:
        logger.error(f"Lỗi khi lưu {filepath}: {str(e)}")

def create_correlation_heatmap(df, output_dir):
   
    logger.info("Đang tạo correlation heatmap...")
    
    # Lấy các cột numerical (loại bỏ cột thời gian và categorical)
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ['month', 'hour', 'day_of_week', 'day_of_year', 'season']
    numerical_cols = [col for col in numerical_cols if col not in exclude_cols]
    
    # Tính ma trận tương quan
    corr_matrix = df[numerical_cols].corr()
    
    # Heatmap đầy đủ
    fig, ax = plt.subplots(figsize=(16, 14))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                cmap='coolwarm', center=0, vmin=-1, vmax=1,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                ax=ax)
    ax.set_title('Ma Trận Tương Quan - Tất Cả Biến', fontsize=16, fontweight='bold')
    save_figure(fig, output_dir / 'correlation_matrix_full.png')
    
    # Heatmap top 10 biến có correlation với temperature
    if 'temperature' in corr_matrix.columns:
        temp_corr = corr_matrix['temperature'].abs().sort_values(ascending=False)
        top_vars = temp_corr.head(10).index.tolist()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix.loc[top_vars, top_vars], annot=True, fmt='.2f',
                    cmap='coolwarm', center=0, vmin=-1, vmax=1,
                    square=True, linewidths=0.5, ax=ax)
        ax.set_title('Ma Trận Tương Quan - Top 10 Biến với Temperature', 
                     fontsize=14, fontweight='bold')
        save_figure(fig, output_dir / 'correlation_matrix_top10.png')
        
        # Lưu thống kê correlation
        with open(output_dir / 'correlation_summary.txt', 'w', encoding='utf-8') as f:
            f.write("TƯƠNG QUAN VỚI TEMPERATURE\n")
            f.write("="*50 + "\n\n")
            for var, corr in temp_corr.items():
                f.write(f"{var:20s}: {corr:6.3f}\n")

def create_scatter_plots(df, output_dir):
    
    logger.info("Đang tạo scatter plots...")
    
    # Lấy mẫu để tăng tốc
    sample_df = df.sample(min(10000, len(df)), random_state=42)
    
    # Định nghĩa các cặp biến cần vẽ
    pairs = [
        ('radiation', 'Bức xạ (Radiation)'),
        ('wind_x', 'Thành phần phía Đông của hướng gió'),
        ('pressure_msl', 'Áp suất (Pressure)'),
        ('wind_y', 'Thành phần phía Bắc của hướng gió')
    ]
    
    # Màu theo mùa
    season_colors = {1: 'green', 2: 'red', 3: 'orange', 4: 'blue'}
    season_names = {1: 'Xuân', 2: 'Hạ', 3: 'Thu', 4: 'Đông'}
    
    for var, label in pairs:
        if var not in sample_df.columns:
            continue
            
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Vẽ scatter plot theo mùa
        for season, color in season_colors.items():
            mask = sample_df['season'] == season
            ax.scatter(sample_df.loc[mask, var], 
                      sample_df.loc[mask, 'temperature'],
                      c=color, label=season_names[season], 
                      alpha=0.5, s=20)
        
        # Thêm đường hồi quy
        z = np.polyfit(sample_df[var].dropna(), 
                       sample_df.loc[sample_df[var].notna(), 'temperature'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(sample_df[var].min(), sample_df[var].max(), 100)
        ax.plot(x_line, p(x_line), "r--", linewidth=2, label='Hồi quy tuyến tính')
        
        # Tính R²
        from sklearn.metrics import r2_score
        y_pred = p(sample_df[var].dropna())
        r2 = r2_score(sample_df.loc[sample_df[var].notna(), 'temperature'], y_pred)
        
        ax.set_xlabel(label, fontsize=12)
        ax.set_ylabel('Nhiệt độ (Temperature)', fontsize=12)
        ax.set_title(f'Mối quan hệ giữa Temperature và {label}\nR² = {r2:.3f}',
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        save_figure(fig, output_dir / f'scatter_temp_vs_{var}.png')

def create_temperature_timeseries(df, output_dir):
    
    logger.info("Đang tạo temperature time series...")
    
    # Chọn 1 tháng đại diện (tháng 7)
    month_data = df[df['month'] == 7].copy()
    month_data = month_data.sort_values('time').head(31*24)  # 1 tháng
    
    if len(month_data) == 0:
        logger.warning("Không có dữ liệu cho tháng 7")
        return
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Vẽ nhiệt độ
    ax.plot(month_data['time'], month_data['temperature'], 
            label='Nhiệt độ', linewidth=1, alpha=0.7)
    
    # Thêm moving average 7 ngày (168 giờ)
    ma_window = min(168, len(month_data) // 2)
    month_data['ma'] = month_data['temperature'].rolling(window=ma_window, center=True).mean()
    ax.plot(month_data['time'], month_data['ma'], 
            label=f'Moving Average ({ma_window}h)', 
            linewidth=2, color='red')
    
    # Đánh dấu max và min
    max_idx = month_data['temperature'].idxmax()
    min_idx = month_data['temperature'].idxmin()
    ax.scatter(month_data.loc[max_idx, 'time'], month_data.loc[max_idx, 'temperature'],
               color='red', s=100, zorder=5, label='Nhiệt độ cao nhất')
    ax.scatter(month_data.loc[min_idx, 'time'], month_data.loc[min_idx, 'temperature'],
               color='blue', s=100, zorder=5, label='Nhiệt độ thấp nhất')
    
    ax.set_xlabel('Thời gian', fontsize=12)
    ax.set_ylabel('Nhiệt độ (chuẩn hóa)', fontsize=12)
    ax.set_title('Chuỗi Thời Gian Nhiệt Độ - Tháng 7', 
                 fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    save_figure(fig, output_dir / 'temperature_timeseries.png')

def create_hourly_heatmap(df, output_dir):
    
    logger.info("Đang tạo hourly heatmap...")
    
    # Nhóm dữ liệu theo giờ và tháng
    hourly_monthly = df.groupby(['hour', 'month'])['temperature'].mean().unstack()
    
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(hourly_monthly, annot=True, fmt='.2f', cmap='YlOrRd',
                cbar_kws={'label': 'Nhiệt độ trung bình'}, ax=ax)
    ax.set_xlabel('Tháng', fontsize=12)
    ax.set_ylabel('Giờ trong ngày', fontsize=12)
    ax.set_title('Heatmap Nhiệt Độ Theo Giờ và Tháng', 
                 fontsize=14, fontweight='bold')
    
    save_figure(fig, output_dir / 'hourly_heatmap.png')

def create_multi_variable_timeseries(df, output_dir):
   
    logger.info("Đang tạo multi-variable time series...")
    
    # Chọn 1 tuần dữ liệu
    week_data = df.sort_values('time').head(7*24).copy()
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    
    variables = [
        ('temperature', 'Nhiệt độ (Temperature)', 'blue'),
        ('humidity', 'Độ ẩm (Humidity)', 'green'),
        ('radiation', 'Bức xạ (Radiation)', 'orange')
    ]
    
    for ax, (var, label, color) in zip(axes, variables):
        if var in week_data.columns:
            ax.plot(week_data['time'], week_data[var], 
                   color=color, linewidth=2)
            ax.set_ylabel(label, fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.set_title(f'Biến động {label} trong 1 tuần', fontsize=12)
    
    axes[-1].set_xlabel('Thời gian', fontsize=12)
    plt.xticks(rotation=45)
    fig.suptitle('Biến Động Nhiều Biến Thời Tiết Theo Thời Gian', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    save_figure(fig, output_dir / 'multi_variable_ts.png')

def create_distribution_plots(df, output_dir):
    
    logger.info("Đang tạo distribution plots...")
    
    variables = ['temperature', 'humidity', 'radiation']
    
    for var in variables:
        if var not in df.columns:
            continue
            
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Vẽ histogram và KDE
        df[var].hist(bins=50, alpha=0.6, density=True, 
                     ax=ax, label='Histogram', color='skyblue')
        df[var].plot(kind='kde', ax=ax, linewidth=2, 
                     label='KDE', color='red')
        
        # Thêm đường normal distribution
        mu, sigma = df[var].mean(), df[var].std()
        x = np.linspace(df[var].min(), df[var].max(), 100)
        ax.plot(x, stats.norm.pdf(x, mu, sigma), 
               'g--', linewidth=2, label='Normal Distribution')
        
        ax.set_xlabel(var.capitalize(), fontsize=12)
        ax.set_ylabel('Mật độ', fontsize=12)
        ax.set_title(f'Phân Phối của {var.capitalize()}', 
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        save_figure(fig, output_dir / f'histogram_{var}.png')

def create_boxplots(df, output_dir):
   
    logger.info("Đang tạo box plots...")
    
    # Box plot theo mùa
    fig, ax = plt.subplots(figsize=(12, 7))
    season_names = {1: 'Xuân', 2: 'Hạ', 3: 'Thu', 4: 'Đông'}
    df['season_name'] = df['season'].map(season_names)
    
    sns.boxplot(data=df, x='season_name', y='temperature', 
                palette='Set2', ax=ax)
    ax.set_xlabel('Mùa', fontsize=12)
    ax.set_ylabel('Nhiệt độ', fontsize=12)
    ax.set_title('Phân Phối Nhiệt Độ Theo Mùa', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    save_figure(fig, output_dir / 'boxplot_season.png')
    
    # Box plot theo điều kiện mưa
    fig, ax = plt.subplots(figsize=(10, 7))
    df['rain_status'] = df['is_rainy'].map({True: 'Có mưa', False: 'Không mưa'})
    
    sns.boxplot(data=df, x='rain_status', y='temperature',
                palette='Set1', ax=ax)
    ax.set_xlabel('Điều kiện thời tiết', fontsize=12)
    ax.set_ylabel('Nhiệt độ', fontsize=12)
    ax.set_title('Phân Phối Nhiệt Độ: Mưa vs Không Mưa', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    save_figure(fig, output_dir / 'boxplot_rain.png')

def create_violin_plot(df, output_dir):
   
    logger.info("Đang tạo violin plot...")
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    sns.violinplot(data=df, x='hour', y='temperature', 
                   palette='viridis', ax=ax)
    ax.set_xlabel('Giờ trong ngày', fontsize=12)
    ax.set_ylabel('Nhiệt độ', fontsize=12)
    ax.set_title('Phân Phối Nhiệt Độ Theo Giờ Trong Ngày', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    save_figure(fig, output_dir / 'violin_hourly.png')

def create_pairplot(df, output_dir):
   
    logger.info("Đang tạo pair plot...")
    
    # Chọn top 5 biến
    top_vars = ['temperature', 'radiation', 'humidity', 'pressure_msl', 'cloud_cover']
    available_vars = [v for v in top_vars if v in df.columns]
    
    if len(available_vars) < 2:
        logger.warning("Không đủ biến để tạo pairplot")
        return
    
    # Lấy mẫu để tăng tốc
    sample_df = df[available_vars + ['season']].sample(min(5000, len(df)), random_state=42)
    
    # Tạo pairplot
    g = sns.pairplot(sample_df, hue='season', palette='Set1',
                     diag_kind='hist', plot_kws={'alpha': 0.6})
    g.fig.suptitle('Pair Plot - Top 5 Biến Quan Trọng', 
                   fontsize=16, fontweight='bold', y=1.01)
    
    save_figure(g.fig, output_dir / 'pairplot_top5.png')

def create_lag_plots(df, output_dir):
   
    logger.info("Đang tạo lag plots...")
    
    # Sắp xếp theo thời gian
    df_sorted = df.sort_values('time').copy()
    
    # Tạo các lag
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for i, lag in enumerate([1, 2, 3]):
        df_sorted[f'temp_lag{lag}'] = df_sorted['temperature'].shift(lag)
        
        axes[i].scatter(df_sorted[f'temp_lag{lag}'], df_sorted['temperature'],
                       alpha=0.3, s=10)
        axes[i].set_xlabel(f'Temperature (t-{lag})', fontsize=11)
        axes[i].set_ylabel('Temperature (t)', fontsize=11)
        axes[i].set_title(f'Lag {lag} Plot', fontsize=12, fontweight='bold')
        axes[i].grid(True, alpha=0.3)
        
        # Thêm đường y=x
        lims = [axes[i].get_xlim(), axes[i].get_ylim()]
        lims = [min(lims[0][0], lims[1][0]), max(lims[0][1], lims[1][1])]
        axes[i].plot(lims, lims, 'r--', alpha=0.5, zorder=0)
    
    plt.tight_layout()
    save_figure(fig, output_dir / 'lag_plot.png')
    
    # ACF plot
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_acf(df_sorted['temperature'].dropna(), lags=50, ax=ax)
    ax.set_title('Autocorrelation Function (ACF) - Temperature', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Lag', fontsize=12)
    ax.set_ylabel('Autocorrelation', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    save_figure(fig, output_dir / 'acf_plot.png')

def create_3d_scatter(df, output_dir):
    
    logger.info("Đang tạo 3D scatter plot...")
    
    # Lấy mẫu
    sample_df = df.sample(min(5000, len(df)), random_state=42)
    
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Màu theo mùa
    season_colors = {1: 'green', 2: 'red', 3: 'orange', 4: 'blue'}
    season_names = {1: 'Xuân', 2: 'Hạ', 3: 'Thu', 4: 'Đông'}
    
    for season, color in season_colors.items():
        mask = sample_df['season'] == season
        ax.scatter(sample_df.loc[mask, 'radiation'],
                  sample_df.loc[mask, 'humidity'],
                  sample_df.loc[mask, 'temperature'],
                  c=color, label=season_names[season], 
                  alpha=0.6, s=20)
    
    ax.set_xlabel('Radiation', fontsize=11)
    ax.set_ylabel('Humidity', fontsize=11)
    ax.set_zlabel('Temperature', fontsize=11)
    ax.set_title('3D Scatter: Temperature vs Radiation vs Humidity', 
                 fontsize=14, fontweight='bold')
    ax.legend()
    
    save_figure(fig, output_dir / '3d_scatter.png')

def create_data_summary(df, output_dir):
   
    logger.info("Đang tạo data summary...")
    
    with open(output_dir / 'data_summary.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TỔNG HỢP THỐNG KÊ DỮ LIỆU THỜI TIẾT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Tổng số dòng dữ liệu: {len(df):,}\n")
        f.write(f"Khoảng thời gian: {df['time'].min()} đến {df['time'].max()}\n")
        f.write(f"Số ngày: {(df['time'].max() - df['time'].min()).days}\n\n")
        
        f.write("THỐNG KÊ MÔ TẢ CÁC BIẾN CHÍNH:\n")
        f.write("-" * 80 + "\n")
        
        numerical_cols = ['temperature', 'humidity', 'radiation', 'pressure_msl', 
                         'windspeed', 'cloud_cover']
        available_cols = [col for col in numerical_cols if col in df.columns]
        
        for col in available_cols:
            f.write(f"\n{col.upper()}:\n")
            f.write(f"  Mean:   {df[col].mean():.4f}\n")
            f.write(f"  Std:    {df[col].std():.4f}\n")
            f.write(f"  Min:    {df[col].min():.4f}\n")
            f.write(f"  25%:    {df[col].quantile(0.25):.4f}\n")
            f.write(f"  Median: {df[col].median():.4f}\n")
            f.write(f"  75%:    {df[col].quantile(0.75):.4f}\n")
            f.write(f"  Max:    {df[col].max():.4f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("PHÂN TÍCH THEO MÙA:\n")
        f.write("-" * 80 + "\n")
        
        season_names = {1: 'Xuân', 2: 'Hạ', 3: 'Thu', 4: 'Đông'}
        for season, name in season_names.items():
            season_data = df[df['season'] == season]
            f.write(f"\n{name}:\n")
            f.write(f"  Số mẫu: {len(season_data):,}\n")
            if 'temperature' in df.columns:
                f.write(f"  Nhiệt độ TB: {season_data['temperature'].mean():.4f}\n")
            if 'humidity' in df.columns:
                f.write(f"  Độ ẩm TB: {season_data['humidity'].mean():.4f}\n")
    
    logger.info("Đã tạo data summary")

def main(input_file='weather_preprocessed.csv', output_base='weather_plots'):
   
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("BẮT ĐẦU QUÁ TRÌNH VISUALIZATION DỮ LIỆU THỜI TIẾT")
    logger.info("=" * 80)
    
    try:
        # 1. Tạo thư mục output
        dirs = create_output_directories(output_base)
        
        # 2. Đọc và xử lý dữ liệu
        df = load_and_preprocess_data(input_file)
        
        # 3. Tạo data summary
        create_data_summary(df, dirs['base'])
        
        # Danh sách các hàm tạo biểu đồ
        visualization_tasks = [
            # Nhóm A: Tương quan
            (create_correlation_heatmap, dirs['correlation'], "Correlation Analysis"),
            (create_scatter_plots, dirs['relationship'], "Scatter Plots"),
            
            # Nhóm B: Chuỗi thời gian
            (create_temperature_timeseries, dirs['timeseries'], "Temperature Time Series"),
            (create_hourly_heatmap, dirs['timeseries'], "Hourly Heatmap"),
            (create_multi_variable_timeseries, dirs['timeseries'], "Multi-variable Time Series"),
            
            # Nhóm C: Phân phối
            (create_distribution_plots, dirs['distribution'], "Distribution Plots"),
            (create_boxplots, dirs['distribution'], "Box Plots"),
            (create_violin_plot, dirs['distribution'], "Violin Plot"),
            
            # Nhóm D: Nâng cao
            (create_pairplot, dirs['advanced'], "Pair Plot"),
            (create_lag_plots, dirs['advanced'], "Lag & ACF Plots"),
            (create_3d_scatter, dirs['advanced'], "3D Scatter Plot"),
        ]
        
        # 4. Tạo các biểu đồ với progress bar
        logger.info("\nĐang tạo các biểu đồ...")
        for func, output_dir, desc in tqdm(visualization_tasks, desc="Overall Progress"):
            try:
                logger.info(f"\n[{desc}] Bắt đầu...")
                func(df, output_dir)
                logger.info(f"[{desc}] Hoàn thành ✓")
            except Exception as e:
                logger.error(f"[{desc}] Lỗi: {str(e)}")
                continue
        
        # 5. Hoàn thành
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("HOÀN THÀNH QUÁ TRÌNH VISUALIZATION")
        logger.info(f"Thời gian thực hiện: {duration:.2f} giây")
        logger.info(f"Các biểu đồ đã được lưu tại: {output_base}/")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n LỖI NGHIÊM TRỌNG: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Thiết lập command-line arguments
    parser = argparse.ArgumentParser(
        description='Script phân tích và visualization dữ liệu thời tiết'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='weather_preprocessed.csv',
        help='Đường dẫn file CSV đầu vào (mặc định: weather_preprocessed.csv)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='weather_plots',
        help='Thư mục lưu output (mặc định: weather_plots)'
    )
    
    args = parser.parse_args()
    
    # Chạy chương trình
    success = main(input_file=args.input, output_base=args.output)
    
    if success:
        print("\n Chương trình hoàn thành thành công!")
        print(f"Kiểm tra các biểu đồ tại thư mục: {args.output}/")
        print(f"Log chi tiết tại: visualization.log")
    else:
        print("\nChương trình gặp lỗi. Kiểm tra file log để biết thêm chi tiết.")