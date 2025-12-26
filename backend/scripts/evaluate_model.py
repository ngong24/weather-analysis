import pickle
import json
import os
import sys
from datetime import datetime

def evaluate_and_compare_models(results_file="model/training_results.json",
                                threshold_r2=0.75,
                                threshold_mae_temp=2.5):
   
    
    try:
        # Load kết quả training mới
        if not os.path.exists(results_file):
            print(f" Không tìm thấy file kết quả: {results_file}")
            return False
        
        with open(results_file, 'r') as f:
            new_results = json.load(f)
        
        print("\n KẾT QUẢ MODEL MỚI:")
        print("=" * 60)
        
        # Đánh giá Temperature Model
        temp_metrics = new_results.get('temperature', {})
        temp_r2 = temp_metrics.get('r2', 0)
        temp_mae = temp_metrics.get('mae', 999)
        temp_rmse = temp_metrics.get('rmse', 999)
        
        print(f" Temperature Model:")
        print(f"   R² Score: {temp_r2:.4f}")
        print(f"   MAE: {temp_mae:.4f}°C")
        print(f"   RMSE: {temp_rmse:.4f}°C")
        
        # Kiểm tra ngưỡng tối thiểu
        is_good = temp_r2 >= threshold_r2 and temp_mae <= threshold_mae_temp
        
        if is_good:
            print(f"   Đạt yêu cầu tối thiểu")
        else:
            print(f"   Không đạt yêu cầu:")
            if temp_r2 < threshold_r2:
                print(f"      R² ({temp_r2:.4f}) < ngưỡng ({threshold_r2})")
            if temp_mae > threshold_mae_temp:
                print(f"      MAE ({temp_mae:.4f}) > ngưỡng ({threshold_mae_temp})")
        
        # Humidity Model 
        if 'humidity' in new_results:
            hum_metrics = new_results['humidity']
            print(f"\n Humidity Model:")
            print(f"   R² Score: {hum_metrics['r2']:.4f}")
            print(f"   MAE: {hum_metrics['mae']:.4f}%")
            print(f"   RMSE: {hum_metrics['rmse']:.4f}%")
        
        # Precipitation Model 
        if 'precipitation' in new_results:
            prec_metrics = new_results['precipitation']
            print(f"\n Precipitation Model:")
            print(f"   R² Score: {prec_metrics['r2']:.4f}")
            print(f"   MAE: {prec_metrics['mae']:.4f}mm")
            print(f"   RMSE: {prec_metrics['rmse']:.4f}mm")
        
        # So sánh với model cũ (nếu có)
        old_results_file = "model/training_results_previous.json"
        if os.path.exists(old_results_file):
            print("SO SÁNH VỚI MODEL CŨ:")   
            with open(old_results_file, 'r') as f:
                old_results = json.load(f)
            old_temp = old_results.get('temperature', {})
            old_r2 = old_temp.get('r2', 0)
            old_mae = old_temp.get('mae', 999)
            
            print(f"Temperature Model:")
            print(f"   R² Score: {old_r2:.4f} → {temp_r2:.4f} ({temp_r2 - old_r2:+.4f})")
            print(f"   MAE: {old_mae:.4f}°C → {temp_mae:.4f}°C ({temp_mae - old_mae:+.4f})")
            
            is_better = temp_r2 >= old_r2 and temp_mae <= old_mae
            
            if is_better:
                print(f"   Model mới tốt hơn!")
            else:
                print(f"   Model mới không cải thiện:")
                if temp_r2 < old_r2:
                    print(f" R² giảm {old_r2 - temp_r2:.4f}")
                if temp_mae > old_mae:
                    print(f" MAE tăng {temp_mae - old_mae:.4f}°C")
                
                # Quyết định có nên giữ model cũ không
                if not is_good:
                    print(f"\n KHÔNG TRIỂN KHAI: Model mới không đạt yêu cầu")
                    return False
                elif temp_r2 < old_r2 - 0.05:  # Giảm quá nhiều
                    print(f"\nKHÔNG TRIỂN KHAI: Model mới kém hơn đáng kể")
                    return False
                else:
                    print(f"\n CÂN NHẮC: Model mới đạt yêu cầu nhưng không tốt hơn")
        else:
            print("\n Không có model cũ để so sánh")
        
        # Lưu metadata
        metadata = {
            'evaluation_date': datetime.now().isoformat(),
            'meets_threshold': is_good,
            'metrics': new_results,
            'thresholds': {
                'r2_min': threshold_r2,
                'mae_temp_max': threshold_mae_temp
            }
        }
        
        with open('model/evaluation_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nĐã lưu metadata đánh giá")
        
        # Kết luận
        if is_good:
            print(" KẾT LUẬN: Model đạt yêu cầu và CÓ THỂ TRIỂN KHAI")
            return True
        else:
            print(" KẾT LUẬN: Model KHÔNG ĐẠT YÊU CẦU - Cần training lại")
            return False
            
    except Exception as e:
        print(f"Lỗi khi đánh giá model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Có thể truyền ngưỡng qua command line
    threshold_r2 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.75
    threshold_mae = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
    
    success = evaluate_and_compare_models(
        threshold_r2=threshold_r2,
        threshold_mae_temp=threshold_mae
    )
    sys.exit(0 if success else 1)