import math

def cas_engineering_design():
    print("="*60)
    print("环境工程学：推流式活性污泥法（CAS）自动化设计程序（采用污泥负荷法）")
    print("="*60)

    # 基础输入参数 (与作业一致)
    Q = 2000              # 进水流量 m3/d
    S0 = 463              # 进水 BOD5 mg/L
    Nk = 40.1             # 进水氨氮 mg/L
    X = 2500              # 混合液污泥浓度 mg/L (取你修正后的 5000)
    SVI = 150             # 污泥指数 mL/g
    r_factor = 1.2        # 修正系数
    f = 0.75              # VSS/SS 比例
    Ce = 20               # 二沉池出水 SS mg/L
    Y = 0.6               # 生长效率
    fb = 0.7              # 进水VSS中可生物降解部分比例
    C0 = 160              # 设计进水VSS mg/L
    eta_w = 0.992         # 剩余污泥含水率
    DO = 2.0              # 溶解氧 mg/L
    Ko = 0.5              # 溶解氧半速率常数
    pH = 7.2              # 水体pH
    Kz = 1.51             # 最大流量系数 (考虑暴雨等极端情况)
    m_weir = 0.32         # 出水堰流量系数 (矩形薄壁堰)
    g = 9.8               # 重力加速度 m/s2
    v_sewage = 0.7        # 进水管流速建议值 m/s
    v_sludge = 0.6        # 污泥管流速建议值 m/s
    b_inlet = 1.6         # 假设进水堰宽 1.6m
    b_return = 1.6        # 假设回流堰宽 1.6m
    b_outlet = 1.6        # 假设出水堰宽 1.6m
    
    # 动力学常数及温度修正 (严格参照教材)
    K2 = 0.025            # 动力学参数，在此假设为不随温度变化的常数
    Kd_20 = 0.06          # 20℃ 时自身氧化系数
    mu_m_15 = 0.5         # 15℃ 时硝化菌最大比生长速率
    Kn_15 = 0.5           # 15℃ 时硝化半速率常数
    bn_20 = 0.04          # 20℃ 时硝化菌衰减系数

    # 曝气系统参数 (教材例题参数)
    alpha = 0.85        # 氧转移系数修正
    beta = 0.95         # 溶解氧饱和度修正
    rho = 0.9           # 海拔900m压力修正系数 (P/P0)
    C_target = 2.0      # 曝气池维持DO mg/L
    Ea = 0.2            # 曝气器利用率 (20%)
    h_diffuser = 4.2    # 曝气头安装深度 m
    P_atm = 0.91 * 10**5 # 900m处大气压 Pa
    
    # 需氧量系数 (教材 AOR 公式系数)
    a_coeff = 1.47      # 去除BOD耗氧
    b_coeff = 4.57      # 硝化耗氧
    c_coeff = 1.42      # 微生物内源呼吸耗氧系数
    
    # 估算出水溶解性 BODe 
    Se_est = 20 - 7.1 * Kd_20 * f * Ce 
    if Se_est < 0: Se_est = 5 # 极低值保护
    eta = (S0 - Se_est) / S0
    Ns = (K2 * Se_est * f) / eta

    print(f"\n[Step 0] 选定污泥负荷 Ns: {Ns:.3f} kgBOD5/(kgMLSS·d)")

    print(f"\n[Step 1] 基本数值计算...")

    V = (Q * S0) / (X * Ns)
    HRT = (V / Q) * 24
    Fv = (Q * S0) / (1000 * V)
    Xr = (10**6 / SVI) * r_factor
    R = X / (Xr - X)
    Se = (Q * S0) / (Q + K2 * X * f * V)

    print(f"   - 曝气池总有效容积 V: {V:.2f} m3")
    print(f"   - 水力停留时间 HRT: {HRT:.2f} h")
    print(f"   - 容积负荷 Fv = {Fv:.2f} kgBOD5/(m3·d)")
    print(f"   - 污泥回流比 R = {R * 100:.1f}%")
    print(f"   - 复核出水溶解性 BOD5 = {Se:.2f} mg/L")

    # ---------------------------------------------------------
    # 3. 季节性出水指标模拟 (夏季 vs 冬季)
    # ---------------------------------------------------------
    print(f"\n[Step 2] 季节性水质与需氧量动态模拟...")
    
    temperatures = {"夏季": 25, "冬季": 5}
    results = {}

    for season, T in temperatures.items():
        # --- A. 动力学温度修正 ---
        mu_m_T = mu_m_15 * math.exp(0.098*(T-15)) * (DO/(Ko+DO)) * (1 - 0.833*(7.2-pH))
        Kn_T = Kn_15 * math.exp(0.118*(T-15))
        bn_T = bn_20 * (1.04 ** (T - 20))
        Kd_T = Kd_20 * (1.04 ** (T - 20))

        # --- B. 污泥产量与污泥龄 ---
        delta_Xv = (Y * Q * (S0 - Se) / 1000) - (Kd_T * V * X * f / 1000)
        delta_Xs = Q * (1 - fb * f) * (C0 - Ce) / 1000
        delta_X = delta_Xv + delta_Xs
        theta_c = (X * V * f) / (1000 * delta_Xv) if delta_Xv > 0 else 999

        # --- C. 硝化核算 (Ne) ---
        mu_n = (1 / theta_c) + bn_T
        if mu_m_T > mu_n:
            Ne = (Kn_T * mu_n) / (mu_m_T - mu_n)
            mode = "硝化反应达标"
            nitrified_N = Nk - Ne # 实际硝化的氨氮量
        else:
            delta_Nw = 0.12 * delta_Xv * 1000 / Q
            Ne = max(0, Nk - delta_Nw)
            mode = "硝化崩溃(仅靠同化)"
            nitrified_N = 0

        # --- D. 需氧量计算 (AOR/SOR/QF) ---
        # 1. AOR (kgO2/d)
        # 公式: AOR = a*(S0-Se)*Q + b*(硝化N)*Q - c*Delta_Xv
        aor_bod = a_coeff * Q * (S0 - Se) / 1000
        aor_nit = b_coeff * (Q * nitrified_N / 1000 - 0.12 * delta_Xv) 
        aor_sludge = c_coeff * delta_Xv
        AOR = aor_bod + max(0, aor_nit) - aor_sludge
        
        # 2. SOR (kgO2/h) 
        # Cs(T) 查表近似公式
        Cs_T = 468 / (31.6 + T) 
        # Ot 逸出氧百分比
        Ot = 21 * (1 - Ea) / (79 + 21 * (1 - Ea)) * 100
        # Pb 曝气头处绝对压力
        Pb = P_atm + 9.8 * 10**3 * h_diffuser
        # Csb(T) 曝气池内平均氧饱和度
        Csb_T = Cs_T * (Pb / (2.026 * 10**5) + Ot / 42)
        
        # SOR 公式转换
        sor_denominator = alpha * (beta * rho * Csb_T - C_target) * (1.024**(T-20))
        SOR = (AOR / 24) * (9.17 / sor_denominator)
        
        # 3. QF (m3/min) 供气量
        # 0.28 是标准状态下每立方米空气含氧量(kg)
        QF = SOR / (0.28 * Ea * 60)

        results[season] = {
            "T": T, "Ne": Ne, "theta_c": theta_c, "mode": mode,
            "delta_X": delta_X, "AOR": AOR, "SOR": SOR, "QF": QF, "Se": Se
        }

    # --- 3. 结果输出 ---
    for season, r in results.items():
        print(f"\n>>> {season}运行核算 (水温 {r['T']}℃ ):")
        print(f"    [水质] NH3-N = {r['Ne']:.2f} mg/L ({r['mode']})")
        print(f"    [运行] 污泥龄 theta_c = {r['theta_c']:.2f} d")
        print(f"    [污泥] 剩余污泥干重 = {r['delta_X']:.2f} kg/d")
        print(f"    [需氧] 实际需氧量 AOR = {r['AOR']:.2f} kgO2/d ({(r['AOR']/24):.2f} kg/h)")
        print(f"    [标准] 标准需氧量 SOR = {r['SOR']:.2f} kgO2/h")
        print(f"    [风量] 鼓风机供气量 QF = {r['QF']:.2f} m3/min")
    # ---------------------------------------------------------
    # 4. 几何结构设计与校核 (GB 50014)
    # ---------------------------------------------------------
    print(f"\n[Step 3] 曝气池物理几何设计...")
    n_tanks = 2           # 2座
    n_corridors = 3       # 3廊道
    h = 3               # 有效水深 m
    
    V_single = V / n_tanks

    # --- 增加建议范围计算逻辑 ---
    print(f"   >>> 设计建议建议如下：")
    # 1. 水深 h 建议：标准推流式 CAS 通常为 3.0 ~ 6.0m
    h_min_std, h_max_std = 3.0, 6.0
    print(f"       1. 有效水深 h: 建议取值范围 {h_min_std} ~ {h_max_std}m (当前设定 h={h}m)")
    
    # 2. 廊道宽 b 的逻辑校核范围
    # 约束 A: 宽深比 1.0 <= b/h <= 2.0  =>  b 需在 [h, 2h]
    b_min_bh = h * 1.0
    b_max_bh = h * 2.0
    
    # 约束 B: 长宽比 5.0 <= L/b <= 10.0
    # 因为 L = V_single / (n_corridors * h * b)，代入 L/b 得到：
    # 5.0 <= V_single / (n_corridors * h * b^2) <= 10.0
    # 反推 b:
    b_max_lb = math.sqrt(V_single / (5.0 * n_corridors * h))
    b_min_lb = math.sqrt(V_single / (10.0 * n_corridors * h))
    
    # 取两个约束的交集
    suggest_b_min = max(b_min_bh, b_min_lb)
    suggest_b_max = min(b_max_bh, b_max_lb)
    
    if suggest_b_min <= suggest_b_max:
        print(f"       2. 廊道宽 b: 在当前水深 h={h}m 下，建议 b 取值范围为 {suggest_b_min:.2f} ~ {suggest_b_max:.2f}m")
    else:
        print(f"       2. [警告]: 在当前水深 h={h}m 下，宽深比和长宽比无法同时满足。建议调整水深或廊道数。")
    print(f"   " + "-"*50)

    A_single = V_single / h
    # 设计廊道宽 b (要求 b/h 在 1~2 之间)
    b = 3.2 
    W_total = b * n_corridors
    L = A_single / W_total
    
    # 校核
    check_bh = b / h
    check_Lb = L / b
    
    print(f"   - 分段设定: {n_tanks}座池子, 每座{n_corridors}廊道")
    print(f"   - 几何尺寸: 单个廊道宽 b={b}m, 有效水深 h={h}m, 长度 L={L:.2f}m")
    print(f"   - 宽深比 b/h = {check_bh:.2f} (规范要求 1.0~2.0) -> {'通过' if 1<=check_bh<=2 else '警告'}")
    print(f"   - 长宽比 L/b = {check_Lb:.2f} (规范要求 5.0~10.0) -> {'通过' if 5<=check_Lb<=10 else '警告'}")

    # ---------------------------------------------------------
    # 5. 出水口水力设计 (严格参照教材 P57)
    # ---------------------------------------------------------
    print(f"\n[Step 4] 进出水口与管路设计 (单池)...")

    def calc_pipe_dia(q, v):
        d = math.sqrt((4 * q) / (math.pi * v))
        return d * 1000   # 转为 mm
        
    def calc_weir_head(q, b_weir):
        # 矩形堰公式: H = (q / (m * b * sqrt(2g)))^(2/3)
        H = (q / (m_weir * b_weir * math.sqrt(2 * g)))**(2/3)
        return H * 100    # 转为 cm

    q_max_1 = Kz * Q / (86400 *n_tanks) 
    # (1) 进水口设计
    H1 = calc_weir_head(q_max_1, b_inlet)
    d1 = calc_pipe_dia(q_max_1, v_sewage)
    
    q_return_2 = R * q_max_1
    # (2) 回流污泥入口设计
    H2 = calc_weir_head(q_return_2, b_return)
    d2 = calc_pipe_dia(q_return_2, v_sludge)
    
    # (3) 出水口设计 (流量 = 进水 + 回流)
    q_total = q_max_1 + q_return_2
    H3 = calc_weir_head(q_total, b_outlet)
    d3 = calc_pipe_dia(q_total, v_sewage)

    print(f"   - 进水口: 管径 d1 ≈ {d1:.0f} mm, 堰上水头 H1: {H1:.2f} cm")
    print(f"   - 回流口: 管径 d2 ≈ {d2:.0f} mm, 堰上水头 H2: {H2:.2f} cm")
    print(f"   - 出水口: 管径 d3 ≈ {d3:.0f} mm, 堰上水头 H3: {H3:.2f} cm")

    # ---------------------------------------------------------
    # 6. 曝气设备布置计算
    # ---------------------------------------------------------
    print(f"\n[Step 5] 曝气设备布置计算...")

    # 1. 确定设计最大供气量 (取夏、冬两季中的较大值进行设备选型)
    QF_max = max(results["夏季"]["QF"], results["冬季"]["QF"])
    QF_min = min(results["夏季"]["QF"], results["冬季"]["QF"])
    print(f"   - 选定设计最大供气量 QF_max = {QF_max:.2f} m3/min ({(QF_max*60):.2f} m3/h)")

    # 2. 曝气器参数设定 (参考教材例题选型)
    q_gas_unit_design = 2.0  # 单个曝气器设计供气量，建议范围 1.5~3.0 m3/(h·个)
    A_serv_min = 0.3         # 单个曝气器最小服务面积 m2/个
    A_serv_max = 0.75        # 单个曝气器最大服务面积 m2/个

    # 3. 计算所需曝气器总数 n_total
    # 总供气量 (m3/h) / 单个曝气器能力
    n_total_calc = (QF_max * 60) / q_gas_unit_design
    
    # 为了安装方便，计算每座池子的数量，并进行向上取整
    n_per_tank = math.ceil(n_total_calc / n_tanks)
    # 进一步平摊到每个廊道 (假设每座池子有 n_corridors 个廊道)
    n_per_corridor = math.ceil(n_per_tank / n_corridors)
    # 修正总数，保证对称布置
    n_total_final = n_per_corridor * n_corridors * n_tanks
    n_per_tank_final = n_per_corridor * n_corridors

    # 4. 核算服务面积
    actual_serv_area = A_single / n_per_tank_final
    
    # 5. 核算供气量范围 (核算另一季节或运行调节是否在设备允许范围内)
    # 教材通常要求单个曝气器供气量在 1.0~5.0 m3/h 之间
    q_actual_max = (QF_max * 60) / n_total_final
    q_actual_min = (QF_min * 60) / n_total_final

    print(f"   - 曝气器选型结果:")
    print(f"     1. 所需曝气器总数: {n_total_final} 个")
    print(f"     2. 布置方案: 每座池子 {n_per_tank_final} 个 (每廊道 {n_per_corridor} 个)")
    print(f"     3. 服务面积核算: {actual_serv_area:.3f} m2/个 (规范要求 {A_serv_min}~{A_serv_max}) -> {'通过' if A_serv_min <= actual_serv_area <= A_serv_max else '警告'}")
    print(f"     4. 最大负荷供气量: {q_actual_max:.2f} m3/(h·个)")
    print(f"     5. 最小负荷供气量: {q_actual_min:.2f} m3/(h·个)")
    print(f"        (核算: 供气量通常需在 1.0~5.0 范围内，确保曝气器不堵塞且充氧有效)")

    # 6. 间距布局建议
    # 假设每廊道布置 2 排
    rows_per_corridor = 2
    n_per_row = math.ceil(n_per_corridor / rows_per_corridor)
    row_spacing = L / n_per_row
    print(f"   - 布局细节建议:")
    print(f"     每廊道布置 {rows_per_corridor} 排，每排 {n_per_row} 个，纵向间距约为 {row_spacing:.2f} m")

    # ---------------------------------------------------------
    # 6. 最终结果输出
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print(f"{'季节':<10} | {'出水 BOD5 (mg/L)':<15} | {'出水 NH3-N (mg/L)':<15} | {'污泥龄 (d)':<10}")
    print("-" * 60)
    for season, data in results.items():
        print(f"{season:<10} | {data['Se']:<18.2f} | {data['Ne']:<18.2f} | {data['theta_c']:<10.2f}")
    print("="*60)

# 执行程序
cas_engineering_design()