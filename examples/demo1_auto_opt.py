import sys
import os
# 将项目根目录加入系统路径，以便识别外层的 cas_engine.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cas_engine import CASConfig, run_cas_engine

if __name__ == "__main__":
    print(">>> 正在启动【自由全维寻优模式】...")
    
    # 仅配置进水边界条件
    config = CASConfig(
        Q=2000,      # 进水流量 (m3/d)
        S0=300,      # 进水 BOD5 (mg/L)
        Nn=40,       # 进水 氨氮 (mg/L)
    )

    # 启动引擎
    run_cas_engine(config)
