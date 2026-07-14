from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from ppcpokp.db import get_db

bp = Blueprint('browse', __name__)

def build_query_conditions(args):
    """
    构建查询条件和参数（不包含表名）
    
    Args:
        args: request.args 对象或字典
    
    Returns:
        tuple: (conditions列表, params列表)
    """
    # 从args获取参数
    def get_arg(key, default=''):
        if hasattr(args, 'get'):
            return args.get(key, default).strip()
        return args.get(key, default).strip() if key in args else default
    
    # 获取所有参数
    model_id = get_arg('model_id')
    model_ids = request.args.getlist('model_ids')
    model_name = get_arg('model_name')
    model_names = request.args.getlist('model_names')
    title = get_arg('title')
    pmid = request.args.getlist('pmid')
    authors = get_arg('authors')
    journal = get_arg('journal')
    country = get_arg('country')
    pub_year = get_arg('pub_year')
    ppc_type = get_arg('ppc_type')
    startYear = get_arg('minYear')
    endYear = get_arg('maxYear')
    model_type = request.args.getlist('model_type')
    model_type_subgroup = request.args.getlist('model_type_subgroup')
    target_outcome = request.args.getlist('target_outcome')
    population_category = request.args.getlist('population_category')
    surgery_discipline = request.args.getlist('surgery_discipline')
    min_variable_number = get_arg('min_variable_number')
    max_variable_number = get_arg('max_variable_number')
    variable_category = request.args.getlist('variable_category')
    timing_prediction = get_arg('timing_prediction')
    application_modality = request.args.getlist('application_modality')

    excellent = get_arg('excellent')
    good = get_arg('good')
    fair = get_arg('fair')
    poor = get_arg('poor')
    overallQuality = get_arg('overallQuality')
    overallApplicability = get_arg('overallApplicability')
    
    conditions = []
    params = []
    
    # 构建条件
    if model_id:
        conditions.append("model_id LIKE ?")
        params.append(f"%{model_id}%")

    if model_ids:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(model_ids))
        conditions.append(f"model_id IN ({placeholders})")
        params.extend(model_ids)  # 注意使用 extend 而不是 append

    if model_name:
        conditions.append("model_name LIKE ?")
        params.append(f"%{model_name}%")
    
    if model_names:
        # 过滤掉空字符串
        valid_names = [name.strip() for name in model_names if name.strip()]
        if valid_names:
            # 创建多个LIKE条件的OR组合
            like_conditions = []
            for name in valid_names:
                like_conditions.append("model_name LIKE ?")
                params.append(f"%{name}%")
            
            # 如果有多个条件，用OR连接
            if len(like_conditions) > 1:
                conditions.append(f"({' OR '.join(like_conditions)})")
            else:
                conditions.append(like_conditions[0])

    if title:
        conditions.append("title LIKE ?")
        params.append(f"%{title}%")

    if pmid:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(pmid))
        conditions.append(f"pmid IN ({placeholders})")
        params.extend(pmid)  # 注意使用 extend 而不是 append

    if authors:
        conditions.append("authors LIKE ?")
        params.append(f"%{authors}%")

    if journal:
        conditions.append("journal_name LIKE ?")
        params.append(f"%{journal}%")

    if country:
        conditions.append("country LIKE ?")
        params.append(f"%{country}%")

    if pub_year:
        conditions.append("publication_year = ?")
        params.append(int(pub_year))

    if ppc_type and ppc_type != 'any':
        conditions.append("ppc_type = ?")
        params.append(ppc_type)

    if startYear:
        conditions.append("publication_year >= ?")
        params.append(int(startYear))

    if endYear:
        conditions.append("publication_year <= ?")
        params.append(int(endYear))

    if model_type:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(model_type))
        conditions.append(f"model_type IN ({placeholders})")
        params.extend(model_type)  # 注意使用 extend 而不是 append

    if model_type_subgroup:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(model_type_subgroup))
        conditions.append(f"model_type_subgroup IN ({placeholders})")
        params.extend(model_type_subgroup)  # 注意使用 extend 而不是 append

    if target_outcome:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(target_outcome))
        conditions.append(f"ppc_type IN ({placeholders})")
        params.extend(target_outcome)  # 注意使用 extend 而不是 append

    if population_category:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(population_category))
        conditions.append(f"population_category IN ({placeholders})")
        params.extend(population_category)  # 注意使用 extend 而不是 append

    if surgery_discipline:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(surgery_discipline))
        conditions.append(f"surgery_discipline IN ({placeholders})")
        params.extend(surgery_discipline)  # 注意使用 extend 而不是 append

    if min_variable_number:
        conditions.append("variable_number >= ?")
        params.append(int(min_variable_number))

    if max_variable_number:
        conditions.append("variable_number <= ?")
        params.append(int(max_variable_number))

    if variable_category:
        for category in variable_category:
            if category == "Patient Baseline Characteristics":
                conditions.append("patient_baseline_characteristics > 0")
            elif category == "Preoperative Clinical & Laboratory Assessment":
                conditions.append("preoperative > 0")
            elif category == "Imaging and Tumor-related Characteristics":
                conditions.append("imaging_tumor > 0")
            elif category == "Surgical and Anesthetic Characteristics":
                conditions.append("surgical_anesthetic > 0")
            elif category == "Intraoperative Course and Monitoring":
                conditions.append("intraoperative > 0")
            elif category == "Early Postoperative Measures and Support":
                conditions.append("early_postoperative > 0")
            elif category == "Risk Scores and Derived Features":
                conditions.append("risk_scores > 0")
            elif category == "Unclassified or Pending Information":
                conditions.append("unclassified > 0")

    if timing_prediction and timing_prediction != 'any':
        conditions.append("timing_prediction = ?")
        params.append(timing_prediction)

    if application_modality:
        # 创建占位符列表，如 "?, ?, ?"
        placeholders = ", ".join(["?"] * len(application_modality))
        conditions.append(f"clinical_application_modality IN ({placeholders})")
        params.extend(application_modality)  # 注意使用 extend 而不是 append


    # 处理 Utlity of model score 的 OR 条件
    # 定义评分等级对应的分数范围映射
    score_ranges = {
        'Excellent': (11, 13),
        'Good': (8, 10),
        'Fair': (4, 7),
        'Poor': (0, 3)
    }

    # 收集所有选择的范围
    selected_ranges = []
    if excellent == 'true':
        selected_ranges.append(score_ranges['Excellent'])
    if good == 'true':
        selected_ranges.append(score_ranges['Good'])
    if fair == 'true':
        selected_ranges.append(score_ranges['Fair'])
    if poor == 'true':
        selected_ranges.append(score_ranges['Poor'])
     # 构建SQL条件
    if selected_ranges:
        range_conditions = []
        for min_score, max_score in selected_ranges:
            range_conditions.append(f"(score BETWEEN {min_score} AND {max_score})")
        
        conditions.append(f"({' OR '.join(range_conditions)})")
    

    if overallQuality and overallQuality != 'any':
        conditions.append("quality = ?")
        if overallQuality == 'high':
            overallQuality = 'High concern regarding quality'
        elif overallQuality == 'low':
            overallQuality = 'Low concern regarding quality'
        elif overallQuality == 'unclear':
            overallQuality = 'Unclear concern regarding quality'
        params.append(overallQuality)

    if overallApplicability and overallApplicability != 'any':
        conditions.append("applicability = ?")
        if overallApplicability == 'high':
            overallApplicability = 'High concern for applicability'
        elif overallApplicability == 'low':
            overallApplicability = 'Low concern for applicability'
        elif overallApplicability == 'unclear':
            overallApplicability = 'Unclear concern for applicability'
        params.append(overallApplicability)

    return conditions, params

def execute_query(table_name, conditions, params, order_by=None):
    """
    执行查询
    
    Args:
        table_name: 查询的表名
        conditions: 查询条件列表
        params: 参数列表
        order_by: 可选，自定义排序字符串，例如 "publication_year ASC, model_name DESC"
                 若未提供，则使用默认排序：publication_year DESC, model_name ASC
    
    Returns:
        list: 查询结果
    """
    # 构建查询
    base_query = f"SELECT * FROM {table_name}"
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    if order_by:
        base_query += f" ORDER BY {order_by}"
    else:
        base_query += " ORDER BY publication_year DESC, model_name ASC"
    
    db = get_db()
    try:
        results = db.execute(base_query, tuple(params)).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        raise Exception(f"Database Error: {str(e)}")

@bp.route('/browse/development')
def development():
    return render_template('browse/development.html')

@bp.route('/browse/development-data', methods=['GET'])
def development_data():
    try:
        conditions, params = build_query_conditions(request.args)
        results = execute_query("development", conditions, params)
        return jsonify(rows=results)
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/browse/development-detail', methods=['GET'])
def development_detail():
    # 获取表单参数
    id = request.args.get('id')

    db = get_db()
    detail = db.execute(
            'SELECT * FROM development WHERE model_id = ?',
            (id,)
    ).fetchone()

    return render_template('browse/partials/development_detail.html', detail=detail)

@bp.route('/browse/validation')
def validation():
    return render_template('browse/validation.html')

@bp.route('/browse/validation-data', methods=['GET'])
def validation_data():
    try:
        conditions, params = build_query_conditions(request.args)
        results = execute_query("validation", conditions, params,"model_name ASC")
        return jsonify(rows=results)
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/browse/validation-detail', methods=['GET'])
def validation_detail():
    # 获取表单参数
    id = request.args.get('id',type=int)

    db = get_db()
    detail = db.execute(
            'SELECT * FROM validation WHERE id = ?',
            (id,)
    ).fetchone()

    return render_template('browse/partials/validation_detail.html', detail=detail)

@bp.route('/browse/comparison')
def comparison():
    return render_template('browse/comparison.html')

@bp.route('/browse/comparison-data', methods=['GET'])
def comparison_data():
    try:
        conditions, params = build_query_conditions(request.args)
        results = execute_query("comparison", conditions, params,"model_name ASC")
        return jsonify(rows=results)
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route('/browse/comparison-detail', methods=['GET'])
def comparison_detail():
    # 字段名映射字典
    field_mapping = {
        'id': 'Model ID',
        'model_name': 'Model Name',
        'model_type': 'Model Type',
        'authors': 'Authors',
        'publication_year': 'Publication Year',
        'algorithm': 'Algorithm',
        "mae": "Mean Absolute Error",
        "mse": "Mean Square Error",
        "rmse": "Root Mean Square Error",
        "maxae": "Maximum Absolute Error",
        "mape": "Mean Absolute Percentage Error",
        "rmsle": "Root Mean Square Logarithmic Error",
        "rae": "Relative Absolute Error",
        "r": "Correlation Coefficient",
        "pcc": "Pearson Correlation Coefficient",
        "srcc": "Spearman’s Rank Correlation Coefficient",
        "r2": "Coefficient of Determination",
        "adjusted_r2": "Adjusted R-Square",
        "f": "F-statistic",
        "aic": "Akaike Information Criterion",
        "bic": "Bayesian Information Criterion",
        "rpd": "Ratio of Standard Deviation to Prediction Error",
        "rc": "Calibration Correlation Coefficient",
        "rp": "Prediction Correlation Coefficient",
        "rmsec": "Root Mean Square Error of Calibration",
        "rmsecv": "Root Mean Square Error of Cross Validation",
        "rmsep": "Root Mean Square Error of Prediction",
        "accuracy": "Accuracy",
        "f1": "F1-score",
        "f_beta": "Fβ-score",
        "oe_ratio": "O/E ratio",
        "auc": "Area Under Curve",
        "ap": "Average Precision",
        "auc_pr": "AUC-PR",
        "brier_score": "Brier Score",
        "log_loss": "Logarithmic Loss",
        "precision": "Precision/Positive Predictive Value",
        "recall": "Recall",
        "sensitivity": "Sensitivity",
        "specificity": "Specificity",
        "youden": "Youden index",
        "cut_off": "Cut-Off Value",
        "negative_predictive": "Negative Predictive Value",
        "lift": "Lift",
        "g_mean": "G-Mean",
        "mcc": "Matthews Correlation Coefficient",
        "kappa": "Kappa Coefficient",
        "calibration_slope": "Calibration slope",
        "hosmer_lemeshow": "Hosmer-Lemeshow p value",
        "aic1": "Akaike Information Criterion",
        "bic1": "Bayesian Information Criterion"
    }

    # 获取表单参数
    id = request.args.get('id',type=int)

    db = get_db()
    detail = db.execute(
            'SELECT * FROM c_literature WHERE id = ?',
            (id,)
    ).fetchone()

    ppc_records = db.execute(
            'SELECT * FROM c_ppc WHERE literature_id = ?',
            (id,)
    ).fetchall()

    
    # 组织数据：为每个PPC获取其所有model记录的字段列表
    result_data = []
    for ppc in ppc_records:
        # 查询对应的model记录
        model_records = db.execute(
            "SELECT id,ppc_id,model_name,model_type,authors,publication_year,algorithm,mae,mse,rmse,maxae,mape,rmsle,rae,r,pcc,srcc,r2,adjusted_r2,f,aic,bic,rpd,rc,rp,rmsec,rmsecv,rmsep,accuracy,f1,f_beta,oe_ratio,auc,ap,auc_pr,brier_score,log_loss,precision,recall,sensitivity,specificity,youden,cut_off,negative_predictive,lift,g_mean,mcc,kappa,calibration_slope,hosmer_lemeshow,aic1,bic1 FROM c_model WHERE ppc_id = ?", 
            (ppc['id'],)
        ).fetchall()
        
        if model_records:
            # 获取所有可能的字段名（从第一个记录中获取）
            all_fields = list(model_records[0].keys())
            
            # 过滤字段：检查每个字段是否在所有model记录中都为空
            fields_to_show = []
            for field in all_fields:
                # 检查该字段是否至少在一个model记录中非空
                has_non_empty = False
                for model in model_records:
                    value = model[field]
                    # 检查值是否非空/非None/非空字符串
                    if value is not None and value != '':
                        has_non_empty = True
                        break
                
                # 如果字段有非空值，并且字段在映射字典中，则保留
                if has_non_empty and field in field_mapping:
                    fields_to_show.append(field)
            
            # 构建垂直表格数据
            table_data = []
            for field in fields_to_show:
                # 获取映射后的字段名
                mapped_field_name = field_mapping.get(field, field)
                row = {'field': mapped_field_name, 'field_original': field}
                
                # 为每个model记录添加该字段的值
                for i, model in enumerate(model_records):
                    value = model[field]
                    # 格式化值：如果是None或空字符串，显示为"-"
                    display_value = value if value not in (None, '') else '-'
                    row[f'model_{i+1}'] = display_value
                
                table_data.append(row)
            
            result_data.append({
                'ppc': ppc,
                'fields_original': fields_to_show,
                'fields_mapped': [field_mapping.get(f, f) for f in fields_to_show],
                'model_records': model_records,
                'table_data': table_data,
                'model_count': len(model_records)
            })
        else:
            result_data.append({
                'ppc': ppc,
                'model_records': [],
                'table_data': [],
                'model_count': 0
            })

    return render_template('browse/partials/comparison_detail.html', detail=detail, data=result_data)