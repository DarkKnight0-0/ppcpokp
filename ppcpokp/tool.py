from flask import Blueprint, render_template, request, jsonify
from .browse import build_query_conditions, execute_query   # 导入公用函数
import re
from ppcpokp.db import get_db

bp = Blueprint('tool', __name__, url_prefix='/tool')

@bp.route('/recommendation', methods=['GET'])
def recommendation():
    """显示推荐表单（GET 请求）"""
    return render_template('tool/recommendation.html')

@bp.route('/development')
def development():
    """渲染结果列表页面"""
    return render_template('tool/development.html')

@bp.route('/development-data')
def development_data():
    try:
        # 1) 获取所有模型记录，后续基于“字段级匹配”计算推荐等级与排序
        results = execute_query("development", [], [])

        if not results:
            return jsonify(rows=[])

        # 2) 辅助函数与映射
        def parse_int(value):
            try:
                if value in (None, ""):
                    return None
                return int(value)
            except (ValueError, TypeError):
                return None

        def norm_text(value):
            return (str(value or "").strip())

        def split_tokens(value):
            # 处理可能的多值字符串：逗号、分号、竖线分隔
            if value is None:
                return []
            raw = str(value)
            parts = re.split(r"[,;|]", raw)
            return [p.strip() for p in parts if p.strip()]

        def match_single(selected, actual):
            return 1 if selected and norm_text(selected) == norm_text(actual) else 0

        def match_multi(selected_values, actual):
            if not selected_values:
                return 0
            selected_set = {norm_text(v) for v in selected_values if norm_text(v)}
            actual_text = norm_text(actual)
            if not actual_text:
                return 0
            if actual_text in selected_set:
                return 1
            actual_tokens = set(split_tokens(actual_text))
            return 1 if actual_tokens.intersection(selected_set) else 0

        category_column_map = {
            "Patient Baseline Characteristics": "patient_baseline_characteristics",
            "Preoperative Clinical & Laboratory Assessment": "preoperative",
            "Imaging and Tumor-related Characteristics": "imaging_tumor",
            "Surgical and Anesthetic Characteristics": "surgical_anesthetic",
            "Intraoperative Course and Monitoring": "intraoperative",
            "Early Postoperative Measures and Support": "early_postoperative",
            "Risk Scores and Derived Features": "risk_scores",
            "Unclassified or Pending Information": "unclassified",
        }

        def match_variable_category(selected_values, dev):
            if not selected_values:
                return 0
            for category in selected_values:
                col = category_column_map.get(category)
                if not col:
                    continue
                value = dev.get(col)
                try:
                    if value is not None and float(value) > 0:
                        return 1
                except (ValueError, TypeError):
                    continue
            return 0

        def normalize_modality(value):
            mapping = {
                "digital implementation tool": "Digital Implementation Tools",
                "digital implementation tools": "Digital Implementation Tools",
                "nomogram-based tool": "Nomogram-Based Tools",
                "nomogram-based tools": "Nomogram-Based Tools",
                "point-based risk score": "Point-Based Risk Scores",
                "point-based risk scores": "Point-Based Risk Scores",
                "algorithm-only model": "Algorithm-Only Models",
                "algorithm-only models": "Algorithm-Only Models",
            }
            key = str(value or "").strip().lower()
            return mapping.get(key, str(value or "").strip())

        # Step 9 默认可用性优先级（仅在特定 tie 情况下生效）
        modality_priority = {
            "Digital Implementation Tools": 1,
            "Nomogram-Based Tools": 2,
            "Point-Based Risk Scores": 3,
            "Algorithm-Only Models": 4,
        }

        def quality_code(text):
            lower = str(text or "").lower()
            if "low concern" in lower:
                return "L"
            if "unclear concern" in lower:
                return "U"
            if "high concern" in lower:
                return "H"
            return "H"

        # Step 8 主排序优先级：
        # (L,L)→(L,U)→(L,H)→(U,L)→(U,U)→(U,H)→(H,L)→(H,U)→(H,H)
        quality_pair_order = {
            ("L", "L"): 1,
            ("L", "U"): 2,
            ("L", "H"): 3,
            ("U", "L"): 4,
            ("U", "U"): 5,
            ("U", "H"): 6,
            ("H", "L"): 7,
            ("H", "U"): 8,
            ("H", "H"): 9,
        }

        def to_level(match_ratio):
            if match_ratio >= 0.75:
                return 3
            if match_ratio >= 0.40:
                return 2
            return 1

        def level_rank(level):
            # Level 3 最优，排序值最小
            return {3: 1, 2: 2, 1: 3}.get(level, 3)

        # 3) 读取用户输入（全部可选）
        basic_population = norm_text(request.args.get("population_category", ""))
        basic_surgery = norm_text(request.args.get("surgery_discipline", ""))
        basic_target = [norm_text(v) for v in request.args.getlist("target_outcome") if norm_text(v)]
        basic_timing = norm_text(request.args.get("timing_prediction", ""))

        adv_model_type = [norm_text(v) for v in request.args.getlist("model_type") if norm_text(v)]
        adv_min_var = parse_int(request.args.get("min_variable_number", ""))
        adv_max_var = parse_int(request.args.get("max_variable_number", ""))
        adv_var_category = [norm_text(v) for v in request.args.getlist("variable_category") if norm_text(v)]
        adv_modality = [normalize_modality(v) for v in request.args.getlist("application_modality") if norm_text(v)]
        user_selected_modality = len(adv_modality) > 0

        # 4) 逐模型计算 Basic / Advanced 匹配
        scored_results = []
        for dev in results:
            # Basic fields
            basic_total = 0
            basic_matched = 0

            if basic_population:
                basic_total += 1
                basic_matched += match_single(basic_population, dev.get("population_category"))

            if basic_surgery:
                basic_total += 1
                basic_matched += match_single(basic_surgery, dev.get("surgery_discipline"))

            if basic_target:
                basic_total += 1
                basic_matched += match_multi(basic_target, dev.get("ppc_type"))

            if basic_timing:
                basic_total += 1
                basic_matched += match_single(basic_timing, dev.get("timing_prediction"))

            basic_ratio = (basic_matched / basic_total) if basic_total else 0
            basic_level = to_level(basic_ratio)

            # Advanced fields
            advanced_total = 0
            advanced_matched = 0

            if adv_model_type:
                advanced_total += 1
                advanced_matched += match_multi(adv_model_type, dev.get("model_type"))

            if adv_min_var is not None or adv_max_var is not None:
                advanced_total += 1
                var_number = parse_int(dev.get("variable_number"))
                if var_number is not None:
                    min_ok = (adv_min_var is None) or (var_number >= adv_min_var)
                    max_ok = (adv_max_var is None) or (var_number <= adv_max_var)
                    advanced_matched += 1 if (min_ok and max_ok) else 0

            if adv_var_category:
                advanced_total += 1
                advanced_matched += match_variable_category(adv_var_category, dev)

            # Clinical Application Modality 仅在用户主动选择时参与计算
            if user_selected_modality:
                advanced_total += 1
                dev_modality = normalize_modality(dev.get("clinical_application_modality"))
                advanced_matched += match_multi(adv_modality, dev_modality)

            advanced_ratio = (advanced_matched / advanced_total) if advanced_total else 0
            advanced_level = to_level(advanced_ratio)

            # Step 6: 整体匹配等级仅由 Basic 决定
            overall_level = basic_level

            # Step 7/8: 方法学质量分级（9类）
            q_code = quality_code(dev.get("quality"))
            a_code = quality_code(dev.get("applicability"))
            quality_pair_rank = quality_pair_order.get((q_code, a_code), 9)

            # Step 9: 仅在“同Overall + 同质量等级 + 未选modality”时作为tie-breaker
            dev_modality_norm = normalize_modality(dev.get("clinical_application_modality"))
            if user_selected_modality:
                availability_rank = 99
            else:
                availability_rank = modality_priority.get(dev_modality_norm, 99)

            # 其他稳定性排序项
            pub_year = parse_int(dev.get("publication_year")) or 0
            auc = dev.get("auc0")
            try:
                auc = float(auc) if auc is not None else 0
            except (ValueError, TypeError):
                auc = 0

            dev["basic_match_ratio"] = round(basic_ratio, 4)
            dev["basic_match_level"] = f"Level {basic_level}"
            dev["advanced_match_ratio"] = round(advanced_ratio, 4)
            dev["advanced_match_level"] = f"Level {advanced_level}"
            dev["overall_match_level"] = f"Level {overall_level}"
            dev["methodology_grade"] = f"({q_code},{a_code})"

            sort_tuple = (
                level_rank(overall_level),
                quality_pair_rank,
                -advanced_level,
                -advanced_ratio,
                availability_rank,
                -auc,
                -pub_year,
            )

            scored_results.append((sort_tuple, dev))

        # 5) 按规则排序并输出前7条
        scored_results.sort(key=lambda x: x[0])
        sorted_results = [item[1] for item in scored_results]
        top7 = sorted_results[:7]

        return jsonify(rows=top7)

    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/comparison')
def comparison():
    """渲染模型比较页面"""
    return render_template('tool/comparison.html')

@bp.route('/comparison-data')
def comparison_data():
    """返回符合筛选条件的模型数据（JSON）"""
    try:
        conditions, params = build_comparison_conditions(request.args)
        results = execute_query("development", conditions, params)
        return jsonify(rows=results)
    except Exception as e:
        return jsonify(error=str(e)), 500

def build_comparison_conditions(args):
    """
    针对 comparison 页面构建查询条件和参数
    支持：pmid（精确）、model_name（模糊）、model_id（精确）、
          population_category（多选）、surgery_discipline（多选）、
          target_outcome（多选）、timing_prediction（多选）、
          variable_number_range（多选区间）、application_modality（多选）
    """
    def get_list(key):
        return args.getlist(key)

    def get_first(key, default=''):
        return args.get(key, default).strip()

    conditions = []
    params = []

    # PMID 精确匹配
    pmid = get_first('pmid')
    if pmid:
        conditions.append("pmid = ?")
        params.append(pmid)

    # 模型名称模糊匹配
    model_name = get_first('model_name')
    if model_name:
        conditions.append("model_name LIKE ?")
        params.append(f"%{model_name}%")

    # 模型编号精确匹配
    model_id = get_first('model_id')
    if model_id:
        conditions.append("model_id = ?")
        params.append(model_id)

    # 患者人群多选
    population = get_list('population_category')
    if population:
        placeholders = ", ".join(["?"] * len(population))
        conditions.append(f"population_category IN ({placeholders})")
        params.extend(population)

    # 手术专科多选
    surgery = get_list('surgery_discipline')
    if surgery:
        placeholders = ", ".join(["?"] * len(surgery))
        conditions.append(f"surgery_discipline IN ({placeholders})")
        params.extend(surgery)

    # 目标结果多选（对应 ppc_type）
    target_outcome = get_list('target_outcome')
    if target_outcome:
        placeholders = ", ".join(["?"] * len(target_outcome))
        conditions.append(f"ppc_type IN ({placeholders})")
        params.extend(target_outcome)

    # 预测时机多选
    timing = get_list('timing_prediction')
    if timing:
        placeholders = ", ".join(["?"] * len(timing))
        conditions.append(f"timing_prediction IN ({placeholders})")
        params.extend(timing)

    # 临床适用模式多选
    modality = get_list('application_modality')
    if modality:
        placeholders = ", ".join(["?"] * len(modality))
        conditions.append(f"clinical_application_modality IN ({placeholders})")
        params.extend(modality)

    # 变量数量区间多选
    ranges = get_list('variable_number_range')
    if ranges:
        range_conditions = []
        for r in ranges:
            if r == '16+':
                range_conditions.append("variable_number >= 16")
            else:
                match = re.match(r'(\d+)-(\d+)', r)
                if match:
                    low, high = match.groups()
                    range_conditions.append(f"(variable_number BETWEEN {low} AND {high})")
        if range_conditions:
            conditions.append("(" + " OR ".join(range_conditions) + ")")

    return conditions, params

@bp.route('/comparison_result')
def comparison_result():
    """展示多个模型的比较结果"""
    model_ids = request.args.getlist('model_id')
    if not model_ids:
        return redirect(url_for('tool.comparison'))

    from .browse import execute_query
    conditions = []
    params = []
    if model_ids:
        placeholders = ", ".join(["?"] * len(model_ids))
        conditions.append(f"model_id IN ({placeholders})")
        params.extend(model_ids)

    try:
        results = execute_query("development", conditions, params)
        # 按传入顺序排序
        id_to_row = {row['model_id']: row for row in results}
        ordered = [id_to_row[mid] for mid in model_ids if mid in id_to_row]
        results = ordered
    except Exception:
        results = []

    return render_template('tool/comparison_result.html', models=results)