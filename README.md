🌊 CAS-AutoOptimizer

Intelligent Design & Optimization Engine for Plug-Flow Conventional Activated
Sludge (CAS) Processes

Python 3.7+ License: MIT PRs Welcome

CAS-AutoOptimizer is a Python-based intelligent engineering calculation and
auto-optimization engine tailored for Environmental Engineering. It focuses on
the forward design and parameter optimization of the Plug-Flow Conventional
Activated Sludge (CAS) process.

Unlike traditional calculators, this engine incorporates a Constraint-Based AI
Extremum-Seeking Algorithm that automatically finds the most economical
structural and aeration layout while strictly adhering to national effluent
standards.

✨ Core Mechanics (Three-Tier Priority System)

The engine's optimization logic strictly follows a three-tier priority
evaluation:

1.  🔴 Priority 1 (Strict Compliance / Fatal Errors): Effluent water quality
    (BOD, NH3-N) must meet the environmental discharge standards. Any design
    failing this is immediately rejected.
2.  🟡 Priority 2 (Process Norms / Warnings): Process parameters (e.g., F/M
    ratio, Volumetric Loading, Return ratio, tank geometry) should ideally fall
    within standard empirical ranges to ensure stable operation.
3.  🟢 Priority 3 (Economic Optimization): Based on satisfying the above
    conditions, the engine seeks the solution with the lowest construction
    (volume) and operational (aeration) costs.

🚀 Key Features

  - Automated Parameter Optimization: Automatically determines the optimal Mixed
    Liquor Suspended Solids (MLSS), Sludge Loading Rate (Ns), tank dimensions,
    and layout.
  - Seasonal Simulation: Simulates process performance (especially nitrification
    limits and aeration demand) across both Summer and Winter conditions.
  - Aeration Network Design: Automatically calculates and balances the total
    aeration units, rows, and spacings required.
  - Engineering Audit System: Generates a comprehensive "health check" report,
    flagging deviations from engineering norms and fatal regulatory violations.
  - Zero Dependencies: Built entirely with Python's standard library (math,
    dataclasses, typing, etc.). No external heavy packages required!

📦 Installation

Since the engine relies only on Python standard libraries, installation is
incredibly simple:

1.  Clone the repository:
    git clone https://github.com/yourusername/CAS-AutoOptimizer.git
    cd CAS-AutoOptimizer
2.  Ensure you have Python 3.7 or higher installed.

💡 Quick Start

You can run the engine in three different modes depending on your needs.

1. Free Full-Dimensional Optimization (Lowest Cost Mode)

Let the engine figure out everything based solely on influent and effluent
boundaries.

from cas_engine import CASConfig, run_cas_engine

# Initialize the config with your project's influent constraints
config = CASConfig(
    Q=2000,      # Influent Flow Rate (m3/d)
    S0=300,      # Influent BOD5 (mg/L)
    Nn=40,       # Influent TN/NH3-N (mg/L)
)

# Run the engine
run_cas_engine(config)

2. Constrained Optimization (e.g., Fixed Volume)

If the footprint of your wastewater treatment plant is limited, lock the total
volume and let the engine optimize the remaining parameters.

config_fixed_v = CASConfig(
    Q=2000, 
    S0=250,       
    Nn=40,
    V_design=5000 # Lock total volume to 5000 m3
)

run_cas_engine(config_fixed_v)

3. Manual Checking Mode (Engineering Audit)

If you already have a complete design and just want the engine to audit it
against engineering norms and seasonal changes.

config_manual = CASConfig(
    Q=2000, S0=200,
    Ns=0.3, X=3000,         # Lock Loading Rate and MLSS
    h=4.5, n_tanks=2,       # Lock Geometry
    n_corridors=3, rows_per_corridor=2
)

run_cas_engine(config_manual)

📊 Sample Output Report

The script generates beautifully formatted Markdown-style reports directly in
your console.

==========================================================================================
     环境工程学：推流式活性污泥法（CAS）智能设计与极值寻优计算书     
==========================================================================================

当前运行模式: 【自由全维寻优模式 (目标:造价最低)】
系统诊断信息: 完美解！出水水质全部达标，工艺参数完全符合规范，且系统已锁定造价/能耗最低方案。

### 第一部分：核心工艺参数极值寻优结果
|  参数类别  |       变量/含义       | 数值 |      单位      |
|------------|-----------------------|------|----------------|
|  寻优结果  |  污泥浓度 MLSS (X)    | 3000 |      mg/L      |
|  寻优结果  |  污泥负荷 Ns          | 0.300|kgBOD/(kgMLSS·d)|
|  基本计算  |  全厂曝气池总容积 V   | 2222.2 |       m3       |
...

### 第四部分：工程设计合规性核验大厅
| 约束级别 |     核验项目    |  实算数值 | 诊断状态 |       合规约束条件       |
|----------|-----------------|-----------|----------|--------------------------|
| 常规规范 |   容积负荷 Fv   |   0.90    |   偏离   |      经验区间 0.3-0.8    |
| 强制红线 |  进水BOD/COD    |   0.67    |   优良   | 极差(必须>=0.25方可生化) |
| 强制红线 | 夏季出水氨氮    |   0.50    |   达标   |      严禁超标 (应<=8)    |
...

 >> [系统黄灯]：妥协运行！出水水质强制标准【已达标】，但有 1 项工艺几何/负荷参数偏离建议规范。

🛠️ Project Structure

  - CASConfig: Dataclass serving as the central parameter hub (Influent,
    Effluent limits, Kinetic constants, Tank geometry).
  - step1_initial_design(): Core forward design calculations (Volume, HRT,
    Return Sludge).
  - step2_seasonal_simulation(): Evaluates temperature-dependent kinetics,
    nitrification limits, and oxygen demands.
  - step3_geometry_and_hydraulics(): Calculates tank dimensions, corridor
    ratios, and pipe diameters.
  - step4_aeration_layout(): Distributes aeration diffusers geometrically.
  - step5_engineering_audit(): The rule engine that outputs Fatal/Warning flags
    based on textbooks and standard codes (e.g., GB18918-2002).
  - auto_optimize_design(): The grid-search AI core leveraging tuple-comparison
    logic for the priority constraints.

⚠️ Disclaimer

This software is provided for educational purposes, conceptual design, and
preliminary engineering evaluations. Real-world wastewater treatment plant
design requires site-specific considerations, advanced modeling (like
BioWin/GPS-X), and certification by licensed professional engineers.

🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check
issues page.

📄 License

This project is licensed under the MIT License - see the LICENSE file for
details.

If you find this project helpful for your environmental engineering studies or
work, please give it a ⭐️!
