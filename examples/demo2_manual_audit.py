import sys
import os
# 将项目根目录加入系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cas_engine import CASConfig, run_cas_engine

if __name__ == "__main__":
    print(">>> 正在启动【全参数锁定图纸校核模式】...")
    
    config_manual = CASConfig(
        Q=2000, S0=200, Nn=40,
        
        # 强制锁死已有图纸/水厂的全部参数
        V_design=3300,          
        Ns=0.3,                 
        X=3000,                 
        h=4.5,                  
        n_tanks=2,              
        n_corridors=3,          
        b_design=6.0,           
        rows_per_corridor=2,    
        n_total_design=1200     
    )

    # 启动诊断
    run_cas_engine(config_manual)
