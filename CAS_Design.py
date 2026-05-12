import math
import os
import copy
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple

# =====================================================================
# 环境工程学：推流式活性污泥法（CAS）智能设计与极值寻优计算引擎
# 
# 核心机制升级：【引入优先级约束】
# 1. 优先级一 (强制红线)：出水水质必须达标 (致命错误致命性最高)。
# 2. 优先级二 (工艺规范)：各结构和负荷参数尽量满足标准区间 (警告错误)。
# 3. 优先级三 (经济代偿)：在满足前两者的基础上，寻找土建或电费代价最低的方案。
# =====================================================================

# =====================================================================
# 1. 数据结构：参数配置中心
# =====================================================================
@dataclass
class CASConfig:
    """环境工程推流式活性污泥法(CAS)参数配置类"""
    
    # [1. 进水与水质参数 (项目边界条件，固定不可寻优)]
    Q: float = 2000              
    S0: float = 200              
    Nn: float = 40               
    COD0: float = 300            
    C0: float = 160              
    pH: float = 7.2              
    
    # [2. 出水与水质参数 (国家环保排放标准，如 GB18918-2002 一级B)]
    Sz: float = 20               
    Nn_e: float = 8              
    COD_e: float = 60            
    Ce: float = 20               

    # [3. 动力学、污泥特性与曝气基础参数 (经验常数或试验测定值)]
    SVI: float = 150             
    r_factor: float = 1.2        
    f: float = 0.75              
    Y: float = 0.6               
    fb: float = 0.7              
    eta_w: float = 0.992         
    DO: float = 2.0              
    Ko: float = 0.5              
    K2: float = 0.025            
    Kd_20: float = 0.06          
    mu_m_15: float = 0.5         
    Kn_15: float = 0.5           
    bn_20: float = 0.04          
    Cs_20: float = 9.17          
    alpha: float = 0.85          
    beta: float = 0.95           
    rho: float = 1.0             
    C_target: float = 2.0        
    Ea: float = 0.2              
    h_diffuser: float = 2.8      
    P_atm: float = 101325        
    a_coeff: float = 1.47        
    b_coeff: float = 4.57        
    c_coeff: float = 1.42        
    Kz: float = 1.51             
    v_sewage: float = 0.7        
    v_sludge: float = 0.6        

    # ==============================================================
    # [4. 核心工艺与工程结构参数 (设为 None 即交由 AI 进行全自动寻优)] 
    # ==============================================================
    V_design: float = None          
    Ns: float = None                
    X: float = None                 
    
    h: float = None                 
    n_tanks: int = None             
    n_corridors: int = None         
    b_design: float = None          
    rows_per_corridor: int = None   
    n_total_design: int = None      
    n_per_row_design: int = None    
    
    # [5. 季节模拟环境]
    temperatures: dict = field(default_factory=lambda: {"夏季": 25, "冬季": 5})

# =====================================================================
# 2. 核心计算逻辑模块 (遵循正向设计原理)
# =====================================================================
def step1_initial_design(cfg: CASConfig) -> Dict[str, Any]:
    V = (cfg.Q * cfg.S0) / (cfg.X * cfg.Ns)
    HRT = (V / cfg.Q) * 24                   
    Fv = (cfg.Q * cfg.S0) / (1000 * V)       
    Xr = (10**6 / cfg.SVI) * cfg.r_factor    
    R = cfg.X / (Xr - cfg.X)                 
    Se_calc = (cfg.Q * cfg.S0) / (cfg.Q + cfg.K2 * cfg.X * cfg.f * V)
    Se_limit = cfg.Sz - 7.1 * cfg.Kd_20 * cfg.f * cfg.Ce 
    return {"Ns": cfg.Ns, "X": cfg.X, "V": V, "HRT": HRT, "Fv": Fv, "R": R, "Se_calc": Se_calc, "Se_limit": Se_limit}

def step2_seasonal_simulation(cfg: CASConfig, V: float, Se_calc: float) -> Dict[str, Any]:
    results = {}
    for season, T in cfg.temperatures.items():
        mu_m_T = cfg.mu_m_15 * math.exp(0.098*(T-15)) * (cfg.DO/(cfg.Ko+cfg.DO)) * (1 - 0.833*(7.2-cfg.pH))
        Kn_T = cfg.Kn_15 * math.exp(0.118*(T-15))      
        bn_T = cfg.bn_20 * (1.04 ** (T - 20))          
        Kd_T = cfg.Kd_20 * (1.04 ** (T - 20))          
        
        delta_Xv = (cfg.Y * cfg.Q * (cfg.S0 - Se_calc) / 1000) - (Kd_T * V * cfg.X * cfg.f / 1000) 
        delta_Xs = cfg.Q * (1 - cfg.fb * cfg.f) * (cfg.C0 - cfg.Ce) / 1000                         
        delta_X = delta_Xv + delta_Xs                                                              
        delta_X_wet = delta_X / ((1 - cfg.eta_w) * 1000)                                           
        
        theta_c = (cfg.X * V * cfg.f) / (1000 * delta_Xv) if delta_Xv > 0 else 999                 
        mu_n = (1 / theta_c) + bn_T                                                                
        
        if mu_m_T > mu_n:
            Ne = (Kn_T * mu_n) / (mu_m_T - mu_n)       
            mode = "硝化正常"
            nitrified_N = cfg.Nn - Ne                  
        else:
            delta_Nw = 0.12 * delta_Xv * 1000 / cfg.Q
            Ne = max(0, cfg.Nn - delta_Nw)
            mode = "硝化受限"
            nitrified_N = 0

        AOR = cfg.a_coeff * cfg.Q * (cfg.S0 - Se_calc) / 1000 + max(0, cfg.b_coeff * (cfg.Q * nitrified_N / 1000 - 0.12 * delta_Xv)) - (cfg.c_coeff * delta_Xv)
        Cs_T = 468 / (31.6 + T)  
        Ot = 21 * (1 - cfg.Ea) / (79 + 21 * (1 - cfg.Ea)) * 100 
        Csb_T = Cs_T * ((cfg.P_atm + 9.8 * 10**3 * cfg.h_diffuser) / (2.026 * 10**5) + Ot / 42) 
        SOR = (AOR / 24) * (cfg.Cs_20 / (cfg.alpha * (cfg.beta * cfg.rho * Csb_T - cfg.C_target) * (1.024**(T-20))))
        QF = SOR / (0.28 * cfg.Ea * 60)

        results[season] = {"T": T, "Ne": Ne, "theta_c": theta_c, "mode": mode, "delta_X_wet": delta_X_wet, "AOR": AOR, "SOR": SOR, "QF": QF, "Se": Se_calc}
    return results

def step3_geometry_and_hydraulics(cfg: CASConfig, V: float, R: float) -> Dict[str, Any]:
    V_single = V / cfg.n_tanks     
    b_min_bh, b_max_bh = cfg.h * 1.0, cfg.h * 2.0                            
    b_max_lb = math.sqrt(V_single / (5.0 * cfg.n_corridors * cfg.h))         
    b_min_lb = math.sqrt(V_single / (10.0 * cfg.n_corridors * cfg.h))        
    suggest_b_min = max(b_min_bh, b_min_lb)
    suggest_b_max = min(b_max_bh, b_max_lb)
    optimal_b = round((suggest_b_min + suggest_b_max) / 2, 1) if suggest_b_min <= suggest_b_max else round(b_min_bh, 1)
    actual_b = cfg.b_design if cfg.b_design is not None else optimal_b
    
    A_single = V_single / cfg.h
    L = A_single / (actual_b * cfg.n_corridors)
    q_max = cfg.Kz * cfg.Q / (86400 * cfg.n_tanks)   
    q_return = R * q_max                             
    calc_d = lambda q, v: math.sqrt((4 * q) / (math.pi * v)) * 1000 
    
    return {"V_single": V_single, "optimal_b": optimal_b, "actual_b": actual_b, "L": L, "A_single": A_single,
            "d_in": calc_d(q_max, cfg.v_sewage), "d_ret": calc_d(q_return, cfg.v_sludge), "d_out": calc_d(q_max+q_return, cfg.v_sewage)}

def step4_aeration_layout(cfg: CASConfig, A_single: float, L: float, sim_results: dict) -> Dict[str, Any]:
    QF_max = max(sim_results["夏季"]["QF"], sim_results["冬季"]["QF"])
    q_gas_unit_design = 2.0  
    symmetry_multiplier = cfg.n_tanks * cfg.n_corridors * cfg.rows_per_corridor 
    conflict_msg = ""
    
    if cfg.n_per_row_design is not None:
        n_per_row = cfg.n_per_row_design
        n_total_final = n_per_row * symmetry_multiplier
        conflict_msg = "人工锁定单列数"
    elif cfg.n_total_design is not None:
        n_per_row = math.ceil(cfg.n_total_design / symmetry_multiplier)
        n_total_final = n_per_row * symmetry_multiplier
        conflict_msg = "依据指定总数纠偏"
    else:
        n_total_calc = (QF_max * 60) / q_gas_unit_design    
        n_per_row = math.ceil(n_total_calc / symmetry_multiplier) 
        n_total_final = n_per_row * symmetry_multiplier
        conflict_msg = "系统自动推演"

    actual_serv_area = A_single / (n_per_row * cfg.rows_per_corridor * cfg.n_corridors) 
    row_spacing = L / n_per_row  
    
    return {"QF_max": QF_max, "n_total_final": n_total_final, "n_per_row": n_per_row, 
            "actual_serv_area": actual_serv_area, "row_spacing": row_spacing, "conflict_msg": conflict_msg}

def step5_engineering_audit(cfg: CASConfig, init_res: dict, sim_res: dict, geo_res: dict, aer_res: dict) -> Tuple[List[Dict], int, int]:
    """步骤五：依据优先级区分【致命错误(出水不达标)】与【警告错误(偏离工艺规范)】"""
    audits = []
    fatal_err = 0  # 优先级1：强制红线错误数
    warn_err = 0   # 优先级2：常规规范错误数
    
    # 1. 容积负荷与可生化性检验
    Fv = init_res['Fv']
    if not (0.3 <= Fv <= 0.8): warn_err += 1
    audits.append({"level": "常规规范", "item": "容积负荷 Fv", "value": f"{Fv:.2f}", "status": "合规" if 0.3 <= Fv <= 0.8 else "偏离", "adv": "经验区间 0.3-0.8"})
    
    bc_ratio = cfg.S0 / cfg.COD0
    if bc_ratio < 0.25: fatal_err += 1
    audits.append({"level": "强制红线", "item": "进水BOD/COD", "value": f"{bc_ratio:.2f}", "status": "优良" if bc_ratio >= 0.25 else "致命", "adv": "极差(必须>=0.25方可生化)"})

    # 2. 出水BOD物理极限检验 (强制水质标准)
    Se_calc = init_res['Se_calc']
    Se_limit = init_res['Se_limit']
    if Se_calc > Se_limit: fatal_err += 1
    audits.append({"level": "强制红线", "item": "动力学出水BOD", "value": f"{Se_calc:.2f}", "status": "达标" if Se_calc <= Se_limit else "违规", "adv": f"严禁超标 (应<={Se_limit:.1f})"})

    # 3. 污泥负荷与回流比检验
    Ns = init_res['Ns']
    if not (0.2 <= Ns <= 0.45): warn_err += 1
    audits.append({"level": "常规规范", "item": "污泥负荷 Ns", "value": f"{Ns:.2f}", "status": "合规" if 0.2 <= Ns <= 0.45 else "偏离", "adv": "经验区间 0.2-0.45"})
    
    R = init_res['R']
    if not (0.4 <= R <= 1.6): warn_err += 1
    audits.append({"level": "常规规范", "item": "污泥回流比 R", "value": f"{R*100:.0f} %", "status": "合规" if 0.4 <= R <= 1.6 else "偏离", "adv": "经验区间 40%-160%"})

    # 4. 季节性氨氮达标检验 (强制水质标准)
    for s, res in sim_res.items():
        if res['Ne'] > cfg.Nn_e: fatal_err += 1
        audits.append({"level": "强制红线", "item": f"{s}出水氨氮", "value": f"{res['Ne']:.2f}", "status": "达标" if res['Ne'] <= cfg.Nn_e else "违规", "adv": f"严禁超标 (应<={cfg.Nn_e})"})
    
    # 5. 构筑物几何与流态审查
    bh_ratio = geo_res['actual_b'] / cfg.h
    lb_ratio = geo_res['L'] / geo_res['actual_b']
    if not (1 <= bh_ratio <= 2): warn_err += 1
    if not (5 <= lb_ratio <= 10): warn_err += 1
    audits.append({"level": "常规规范", "item": "宽深比 b/h", "value": f"{bh_ratio:.2f}", "status": "合规" if 1 <= bh_ratio <= 2 else "偏离", "adv": "建议区间 1~2"})
    audits.append({"level": "常规规范", "item": "长宽比 L/b", "value": f"{lb_ratio:.2f}", "status": "合规" if 5 <= lb_ratio <= 10 else "偏离", "adv": "建议区间 5~10"})
                   
    return audits, fatal_err, warn_err

# =====================================================================
# 3. 核心 AI 智能寻优引擎 (基于优先级的降维打击比对)
# =====================================================================
def auto_optimize_design(original_cfg: CASConfig) -> Tuple[CASConfig, bool, str]:
    
    pool_X = [2000, 2500, 3000, 3500, 4000, 4500, 5000] if original_cfg.X is None else [original_cfg.X]
    pool_Ns = [0.20, 0.25, 0.30, 0.35, 0.40] if original_cfg.Ns is None else [original_cfg.Ns]
    pool_h = [3.0, 4.0, 5.0, 6.0] if original_cfg.h is None else [original_cfg.h]
    pool_tanks = [2, 3, 4] if original_cfg.n_tanks is None else [original_cfg.n_tanks]
    pool_corridors = [2, 3, 4] if original_cfg.n_corridors is None else [original_cfg.n_corridors]
    pool_rows = [2, 3] if original_cfg.rows_per_corridor is None else [original_cfg.rows_per_corridor]
    
    best_cfg = None
    # 设定最高初始壁垒
    best_score = (999, 999, float('inf'))  # 格式: (致命错误数, 警告错误数, 经济代价)
    
    for x in pool_X:
        if original_cfg.V_design is not None:
            calc_ns = (original_cfg.Q * original_cfg.S0) / (original_cfg.V_design * x)
            ns_list = [calc_ns]
        else:
            ns_list = pool_Ns
            
        for ns in ns_list:
            for h in pool_h:
                for t in pool_tanks:
                    for c in pool_corridors:
                        for r in pool_rows:
                            test_cfg = copy.deepcopy(original_cfg)
                            test_cfg.Ns, test_cfg.X = ns, x
                            test_cfg.h, test_cfg.n_tanks, test_cfg.n_corridors, test_cfg.rows_per_corridor = h, t, c, r
                            
                            try:
                                i_res = step1_initial_design(test_cfg)
                                s_res = step2_seasonal_simulation(test_cfg, i_res['V'], i_res['Se_calc'])
                                g_res = step3_geometry_and_hydraulics(test_cfg, i_res['V'], i_res['R'])
                                a_res = step4_aeration_layout(test_cfg, g_res['A_single'], g_res['L'], s_res)
                                
                                _, fatal_err, warn_err = step5_engineering_audit(test_cfg, i_res, s_res, g_res, a_res)
                                
                                # 经济代价函数
                                current_cost = i_res['V'] if original_cfg.V_design is None else test_cfg.X
                                
                                # 【核心逻辑：元组比较机制】
                                # Python中比较 (A1, B1, C1) < (A2, B2, C2) 时，会严格按从左到右的优先级进行。
                                # 这意味着只要 fatal_err 更小，它就能碾压一切其他的偏离。
                                current_score = (fatal_err, warn_err, current_cost)
                                
                                if current_score < best_score:
                                    best_score = current_score
                                    best_cfg = copy.deepcopy(test_cfg)
                                    
                            except Exception:
                                continue 
                                
    # 解析最终得出的最好成绩
    final_fatal, final_warn, final_cost = best_score
    
    if final_fatal == 0:
        if final_warn == 0:
            msg = "完美解！出水水质全部达标，工艺参数完全符合规范，且系统已锁定造价/能耗最低方案。"
        else:
            msg = f"次优妥协解：【水质已保证达标！】受限于边界条件，有 {final_warn} 处工艺尺寸/负荷参数偏离经验规范，但整体安全。"
        return best_cfg, True, msg
    else:
        return best_cfg, False, f"无解崩溃：无论如何调整设备池体，水质依然有 {final_fatal} 项红线指标严重违规！(通常因为容积被锁死且太小，或进水B/C过低)"

# =====================================================================
# 4. 报告生成引擎与主程序编排
# =====================================================================
def generate_report(cfg: CASConfig, init_res, sim_res, geo_res, aer_res, audits, f_err, w_err, sys_msg, mode) -> str:
    lines = []
    def make_table(headers, rows):
        col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *rows)]
        col_widths = [w + 4 for w in col_widths] 
        sep = "|" + "|".join("-" * w for w in col_widths) + "|"
        t_lines = ["|" + "|".join(f"{str(h).center(w)}" for h, w in zip(headers, col_widths)) + "|", sep]
        for row in rows:
            t_lines.append("|" + "|".join(f" {str(item).ljust(w-1)}" for item, w in zip(row, col_widths)) + "|")
        return "\n".join(t_lines)

    lines.append("="*90)
    lines.append(f"{'环境工程学：推流式活性污泥法（CAS）智能设计与极值寻优计算书':^80}")
    lines.append("="*90)
    lines.append(f"\n当前运行模式: 【{mode}】")
    lines.append(f"系统诊断信息: {sys_msg}\n")

    lines.append("### 第一部分：核心工艺参数极值寻优结果\n")
    headers1 = ["参数类别", "变量/含义", "数值", "单位"]
    rows1 = [
        ["寻优结果", "污泥浓度 MLSS (X)", f"{init_res['X']:.0f}", "mg/L"],
        ["寻优结果", "污泥负荷 Ns", f"{init_res['Ns']:.3f}", "kgBOD/(kgMLSS·d)"],
        ["基本计算", "全厂曝气池总容积 V", f"{init_res['V']:.1f}", "m3"],
        ["基本计算", "水力停留时间 HRT", f"{init_res['HRT']:.2f}", "h"],
        ["基本计算", "容积负荷 Fv", f"{init_res['Fv']:.3f}", "kgBOD/(m3·d)"],
        ["基本计算", "污泥回流比 R", f"{init_res['R']*100:.1f}", "%"],
    ]
    lines.append(make_table(headers1, rows1) + "\n\n")

    lines.append("### 第二部分：季节性工艺参数模拟\n")
    headers2 = ["参数名称", "夏季工况", "冬季工况", "单位/说明"]
    rows2 = [
        ["污水温度 T", f"{sim_res['夏季']['T']} ℃", f"{sim_res['冬季']['T']} ℃", "-"],
        ["硝化状态", sim_res['夏季']['mode'], sim_res['冬季']['mode'], "-"],
        ["出水氨氮 Ne", f"{sim_res['夏季']['Ne']:.2f}", f"{sim_res['冬季']['Ne']:.2f}", "mg/L"],
        ["出水 BOD5 Se", f"{sim_res['夏季']['Se']:.2f}", f"{sim_res['冬季']['Se']:.2f}", "mg/L"],
        ["污泥龄 SRT", f"{sim_res['夏季']['theta_c']:.1f}", f"{sim_res['冬季']['theta_c']:.1f}", "d"],
        ["产湿泥量", f"{sim_res['夏季']['delta_X_wet']:.1f}", f"{sim_res['冬季']['delta_X_wet']:.1f}", "kg/d"],
        ["需风量 QF", f"{sim_res['夏季']['QF']:.1f}", f"{sim_res['冬季']['QF']:.1f}", "m3/min"],
    ]
    lines.append(make_table(headers2, rows2) + "\n\n")

    lines.append("### 第三部分：工程构筑物设计与曝气网络\n")
    headers3 = ["工程模块", "结构部件", "最终采用值", "状态说明"]
    rows3 = [
        ["构筑物", "全厂总座数", f"{cfg.n_tanks} 座", "-"], 
        ["构筑物", "单座容积", f"{geo_res['V_single']:.1f} m3", "-"], 
        ["构筑物", "有效水深 h", f"{cfg.h} m", "-"],
        ["构筑物", "单座内廊道数量", f"{cfg.n_corridors} 条", "-"],
        ["构筑物", "单条廊道宽 b", f"{geo_res['actual_b']} m", "-"],
        ["构筑物", "单条廊道长 L", f"{geo_res['L']:.2f} m", "-"],
        ["曝气系统", "全厂曝气器总数", f"{aer_res['n_total_final']} 个", aer_res['conflict_msg']], 
        ["曝气系统", "单列纵向个数", f"{aer_res['n_per_row']} 个", "-"],
    ]
    lines.append(make_table(headers3, rows3) + "\n\n")

    lines.append("### 第四部分：工程设计合规性核验大厅\n")
    headers4 = ["约束级别", "核验项目", "实算数值", "诊断状态", "合规约束条件"]
    rows4 = [[a['level'], a['item'], a['value'], a['status'], a['adv']] for a in audits]
    lines.append(make_table(headers4, rows4) + "\n")
    
    # 动态结语判定
    if f_err == 0 and w_err == 0:
        lines.append(" >> [系统绿灯]：完美无瑕！水质红线要求与全部工程规范审查均通过。")
    elif f_err == 0 and w_err > 0:
        lines.append(f" >> [系统黄灯]：妥协运行！出水水质强制标准【已达标】，但有 {w_err} 项工艺几何/负荷参数偏离建议规范。")
    else:
        lines.append(f" >> [系统红灯]：设计报废！查出 {f_err} 项水质出水指标严重违规，{w_err} 项工艺偏离，严禁投建！")

    return "\n".join(lines)


def run_cas_engine(config: CASConfig):
    check_list = [config.Ns, config.X, config.h, config.n_tanks, config.n_corridors, config.rows_per_corridor]
    all_locked = all(v is not None for v in check_list)
    
    if all_locked:
        mode_str = "人工强制核算模式"
        working_cfg = config
        is_success = True
        sys_msg = "所有参数均已人工输入，系统关闭 AI 寻优，仅执行合规诊断。"
    else:
        if config.V_design is not None:
            mode_str = f"定容积约束寻优模式 (V={config.V_design}m3)"
        else:
            mode_str = "自由全维寻优模式 (目标:造价最低)"
            
        working_cfg, is_success, sys_msg = auto_optimize_design(config)

    i_res = step1_initial_design(working_cfg)
    s_res = step2_seasonal_simulation(working_cfg, i_res['V'], i_res['Se_calc'])
    g_res = step3_geometry_and_hydraulics(working_cfg, i_res['V'], i_res['R'])
    a_res = step4_aeration_layout(working_cfg, g_res['A_single'], g_res['L'], s_res)
    
    audits, f_err, w_err = step5_engineering_audit(working_cfg, i_res, s_res, g_res, a_res)
    
    if not is_success and not all_locked:
        # 如果寻优崩溃，给前台输出明确失败标识
        f_err = 99 
        
    report_text = generate_report(working_cfg, i_res, s_res, g_res, a_res, audits, f_err, w_err, sys_msg, mode_str)
    print(report_text)

# =====================================================================
# 5. 执行示例入口
# =====================================================================
if __name__ == "__main__":
    
    cfg_fixed_v = CASConfig(
        Q=2000, 
        S0=700,       
        Nn=40,
    )
    run_cas_engine(cfg_fixed_v)