from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from ppcpokp.db import get_db
from collections import defaultdict
import re
from collections import Counter
from flask import jsonify
import networkx as nx
import community.community_louvain as community
import statistics

bp = Blueprint('chart', __name__)

@bp.route('/chart')
def index():
    return render_template('chart/index.html')

@bp.route('/chart/year-model-data')
def year_model_data():
    """从数据库获取数据并转换为ECharts格式"""
    db = get_db()
    try:
        # 查询数据：获取每个年份、每种模型类型的数量
        query = """
        SELECT publication_year, model_type, COUNT(*) as count
        FROM development
        WHERE publication_year IS NOT NULL
          AND publication_year != ''
          AND model_type IS NOT NULL
          AND model_type != ''
        GROUP BY publication_year, model_type
        ORDER BY publication_year, model_type
        """
        
        results = db.execute(query).fetchall()
        
        if not results:
            return jsonify({'error': 'No data found'}), 404
        
        # 处理数据
        data_by_year = defaultdict(dict)
        all_model_types = set()
        
        for row in results:
            year = row['publication_year']
            model_type = row['model_type']
            count = row['count']
            
            # 确保年份为整数
            try:
                year = int(year)
            except (ValueError, TypeError):
                continue
            
            # 标准化模型类型名称（处理大小写不一致问题）
            if model_type.lower() == 'traditional statistical model':
                model_type = 'Traditional Statistical Model'
                
            data_by_year[year][model_type] = count
            all_model_types.add(model_type)
        
        # 如果数据为空，返回错误
        if not data_by_year:
            return jsonify({'error': 'No valid data found'}), 404
        
        # 获取最小和最大年份，填充缺失的年份
        min_year = min(data_by_year.keys())
        max_year = max(data_by_year.keys())
        years = list(range(min_year, max_year + 1))
        
        # 为缺失年份创建空数据
        for year in years:
            if year not in data_by_year:
                data_by_year[year] = {}
        
        # 重新排序年份
        years = sorted(data_by_year.keys())
        
        # 获取排序后的模型类型列表
        model_types = sorted(list(all_model_types))
        
        # 预定义颜色列表
        colors = [
            '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
            '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#60c2ef'
        ]
        
        # 为每种模型类型创建数据序列
        series_data = []
        
        for i, model_type in enumerate(model_types):
            series_item = {
                'name': model_type,
                'type': 'bar',
                'stack': 'total',
                'emphasis': {
                    'focus': 'series'
                },
                'itemStyle': {
                    'color': colors[i % len(colors)]
                },
                'data': []
            }
            
            # 为每个年份添加数据
            for year in years:
                count = data_by_year[year].get(model_type, 0)
                series_item['data'].append(count)
            
            series_data.append(series_item)
        
        # 计算总数
        total_models = 0
        for series in series_data:
            total_models += sum(series['data'])
        
        # 构建响应数据
        chart_data = {
            'years': years,
            'series': series_data,
            'model_types': model_types,
            'total_models': total_models
        }
        
        # 直接返回数据对象，而不是嵌套在rows中
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/country-top5-data')
def country_top5_data():
    """获取国家排名前5的数据（横向条形图用）"""
    db = get_db()
    try:
        query = """
        SELECT country, COUNT(*) as count
        FROM development
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country
        ORDER BY count DESC
        LIMIT 5
        """
        results = db.execute(query).fetchall()
        
        if not results:
            return jsonify({'error': 'No country data found'}), 404

        countries = []
        counts = []
        for row in results:
            country = row['country']
            count = row['count']
            countries.append(country)
            counts.append(count)

        return jsonify({
            'countries': countries,
            'counts': counts,
            'total': sum(counts)
        })
    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()


# 简单的英文停用词列表
STOPWORDS = set([
    # 基础英语停用词
    'the', 'and', 'of', 'to', 'a', 'in', 'for', 'is', 'on', 'that', 'by',
    'this', 'with', 'i', 'you', 'it', 'not', 'or', 'be', 'are', 'from',
    'at', 'as', 'have', 'but', 'was', 'we', 'an', 'will', 'can', 'all',
    'their', 'there', 'been', 'has', 'had', 'were', 'which', 'such', 'only',
    'one', 'two', 'more', 'very', 'when', 'also', 'than', 'other', 'some',
    'these', 'those', 'into', 'over', 'after', 'before', 'most', 'any', 'use',

    # 学术文献高频通用词（从你的词汇表中提取）
    'used', 'using', 'based', 'associated','included', 'including','our'
])

@bp.route('/chart/wordcloud-data')
def wordcloud_data():
    """从 abstract 列生成词频数据，返回 ECharts wordCloud 格式"""
    db = get_db()
    try:
        # 获取所有非空的 abstract 文本
        rows = db.execute(
            """
            SELECT MAX(abstract) as abstract 
            FROM development 
            WHERE abstract IS NOT NULL AND abstract != '' 
            GROUP BY literature_id
            """
        ).fetchall()

        if not rows:
            return jsonify({'error': 'No abstract data found'}), 404

        # 合并所有 abstract，并分词
        all_words = []
        for row in rows:
            text = row['abstract']
            # 只保留字母字符（英文单词），转为小写
            words = re.findall(r"[a-zA-Z]+", text.lower())
            all_words.extend(words)

        # 统计词频，排除停用词和过短的词（长度 < 3）
        word_counts = Counter(
            word for word in all_words 
            if word not in STOPWORDS and len(word) > 2
        )

        # 取前 100 个高频词
        top_words = word_counts.most_common(100)

        # 转换为 ECharts wordCloud 所需的格式：[ { name: word, value: count }, ... ]
        data = [{'name': word, 'value': count} for word, count in top_words]

        return jsonify(data)

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/sankey-data')
def sankey_data():
    """返回桑基图数据，支持最小计数过滤"""
    min_count = request.args.get('min_count', 3, type=int)
    db = get_db()
    try:
        # 查询三层数据（SQL 保持不变）
        query1 = """
        SELECT surgery_discipline, timing_prediction, COUNT(*) as cnt
        FROM development
        WHERE surgery_discipline IS NOT NULL AND surgery_discipline != ''
          AND timing_prediction IS NOT NULL AND timing_prediction != ''
        GROUP BY surgery_discipline, timing_prediction
        """
        rows1 = db.execute(query1).fetchall()

        query2 = """
        SELECT timing_prediction, ppc_type, COUNT(*) as cnt
        FROM development
        WHERE timing_prediction IS NOT NULL AND timing_prediction != ''
          AND ppc_type IS NOT NULL AND ppc_type != ''
        GROUP BY timing_prediction, ppc_type
        """
        rows2 = db.execute(query2).fetchall()

        query3 = """
        SELECT ppc_type, model_type, COUNT(*) as cnt
        FROM development
        WHERE ppc_type IS NOT NULL AND ppc_type != ''
          AND model_type IS NOT NULL AND model_type != ''
        GROUP BY ppc_type, model_type
        """
        rows3 = db.execute(query3).fetchall()

        links = []
        node_names = set()

        # 处理第一层（手术专科 → 预测时机）
        for row in rows1:
            if row['cnt'] >= min_count:
                source = f"Surgery: {row['surgery_discipline']}"
                target = f"Timing: {row['timing_prediction']}"
                value = row['cnt']
                node_names.update([source, target])
                links.append({"source": source, "target": target, "value": value})

        # 处理第二层（预测时机 → 结局类型）
        for row in rows2:
            if row['cnt'] >= min_count:
                source = f"Timing: {row['timing_prediction']}"
                target = f"Outcome: {row['ppc_type']}"
                value = row['cnt']
                node_names.update([source, target])
                links.append({"source": source, "target": target, "value": value})

        # 处理第三层（结局类型 → 模型类型）
        for row in rows3:
            if row['cnt'] >= min_count:
                source = f"Outcome: {row['ppc_type']}"
                target = f"Model: {row['model_type']}"
                value = row['cnt']
                node_names.update([source, target])
                links.append({"source": source, "target": target, "value": value})

        if not links:
            return jsonify({'error': 'No data meeting minimum count'}), 404

        nodes = [{"name": name} for name in sorted(node_names)]

        return jsonify({"nodes": nodes, "links": links})

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/coauthor-network')
def coauthor_network():
    """
    从 development 表读取 Author 字段，构建作者合作网络，
    进行社区检测，返回 ECharts 关系图所需的 JSON 数据。
    
    查询参数：
        min_degree (int): 节点最小加权度，默认 15，过滤孤立/低度节点
        min_cooperation (int): 边的最小合作次数，默认 1，只保留合作次数 >= 该值的边
    """
    db = get_db()
    try:
        # 获取所有非空的 Author 字段
        rows = db.execute(
            "SELECT authors FROM development WHERE authors IS NOT NULL AND authors != '' GROUP BY literature_id"
        ).fetchall()
        if not rows:
            return jsonify({'error': 'No author data found'}), 404

        # 统计作者对合作次数
        pair_counts = defaultdict(int)
        author_set = set()

        for row in rows:
            authors_str = row['authors']
            authors = [a.strip() for a in authors_str.split(';') if a.strip()]
            for i in range(len(authors)):
                for j in range(i+1, len(authors)):
                    pair = tuple(sorted([authors[i], authors[j]]))
                    pair_counts[pair] += 1
            author_set.update(authors)

        # 构建 networkx 图
        G = nx.Graph()
        for author in author_set:
            G.add_node(author)
        for (a1, a2), weight in pair_counts.items():
            G.add_edge(a1, a2, weight=weight)

        # ----- 新增：筛选作者合作次数（边权重）-----
        min_cooperation = request.args.get('min_cooperation', 1, type=int)
        if min_cooperation > 1:
            edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d.get('weight', 1) < min_cooperation]
            G.remove_edges_from(edges_to_remove)

        # 可选：过滤掉孤立节点或低度节点（防止前端卡顿）
        min_degree = request.args.get('min_degree', 1, type=int)
        nodes_to_keep = [n for n, d in G.degree(weight='weight') if d >= min_degree]
        G = G.subgraph(nodes_to_keep)

        # Louvain 社区检测（基于权重）
        partition = community.best_partition(G, weight='weight')

        # 准备 ECharts 数据
        nodes = []
        categories = set(partition.values())

        for node, comm_id in partition.items():
            degree = G.degree(node, weight='weight')
            symbol_size = 10 + 2 * degree
            nodes.append({
                "name": node,
                "category": comm_id,
                "value": degree,
                "symbolSize": symbol_size
            })

        links = []
        for u, v, data in G.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "value": data.get('weight', 1)
            })

        cat_list = [{"name": f"Cluster {i}"} for i in sorted(categories)]

        return jsonify({
            "nodes": nodes,
            "links": links,
            "categories": cat_list
        })

    except Exception as e:
        return jsonify(error=f"Coauthor network error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/heatmap-data')
def heatmap_data():
    """返回热图数据：纵轴 model_type，横轴 clinical_application_modality，值 median auc0
    对于样本量不足的组合，value 返回 None，前端将显示为灰色格子。
    """
    db = get_db()
    MIN_COUNT = 3   # 最小样本量阈值

    try:
        # 获取所有非空的 model_type 和 clinical_application_modality 以及 auc0
        rows = db.execute("""
            SELECT model_type, clinical_application_modality, auc0
            FROM development
            WHERE model_type IS NOT NULL AND model_type != ''
              AND clinical_application_modality IS NOT NULL AND clinical_application_modality != ''
        """).fetchall()

        # 收集所有可能的 model_type 和 clinical_application_modality
        model_types = set()
        impl_formats = set()
        combo_data = defaultdict(lambda: {'aucs': [], 'count': 0})

        for row in rows:
            mt = row['model_type']
            im = row['clinical_application_modality']
            auc = row['auc0']

            model_types.add(mt)
            impl_formats.add(im)

            key = (mt, im)
            combo_data[key]['count'] += 1
            if auc is not None:
                combo_data[key]['aucs'].append(auc)

        # 转换为有序列表，用于坐标轴
        model_types = sorted(model_types)
        impl_formats = sorted(impl_formats)

        # 构建系列数据：为每一个格子都生成一条记录
        series_data = []
        for y_idx, mt in enumerate(model_types):
            for x_idx, im in enumerate(impl_formats):
                key = (mt, im)
                data = combo_data.get(key, {'aucs': [], 'count': 0})
                total = data['count']
                aucs = data['aucs']

                # 判断样本量是否足够
                if total >= MIN_COUNT and aucs:
                    # 计算中位数
                    median = statistics.median(aucs)
                    series_data.append({
                        'value': [x_idx, y_idx, median],
                        'count': total
                    })
                else:
                    # 样本量不足或无有效 AUC → 无效格子，value 设为 None
                    series_data.append({
                        'value': [x_idx, y_idx, None],
                        'count': total
                    })

        return jsonify({
            'xAxis': impl_formats,
            'yAxis': model_types,
            'data': series_data
        })

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/model-subgroup-treemap')
def model_subgroup_treemap():
    """
    返回模型亚分类矩形树图数据。
    按 model_type (大类) 分组，每个大类下包含多个 model_type_subgroup (亚分类)，
    每个亚分类有一个 count。
    为相同大类分配同一颜色（颜色预定义列表）。
    """
    db = get_db()
    try:
        # 查询每个大类+亚分类的计数
        query = """
        SELECT model_type, model_type_subgroup, COUNT(*) as cnt
        FROM development
        WHERE model_type IS NOT NULL AND model_type != ''
          AND model_type_subgroup IS NOT NULL AND model_type_subgroup != ''
        GROUP BY model_type, model_type_subgroup
        ORDER BY model_type, model_type_subgroup
        """
        rows = db.execute(query).fetchall()
        if not rows:
            return jsonify({'error': 'No subgroup data found'}), 404

        # 按大类组织数据
        groups = defaultdict(list)
        for row in rows:
            model_type = row['model_type']
            subgroup = row['model_type_subgroup']
            count = row['cnt']
            groups[model_type].append({
                'name': subgroup,
                'value': count
            })

        # 预定义颜色列表（可根据需要扩充）
        colors = [
            '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
            '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#60c2ef',
            '#d48265', '#749f83', '#ca8622', '#bda29a', '#6e7074'
        ]

        # 构建 treemap 数据：每个大类作为一个节点，包含 children 和 color
        treemap_data = []
        for i, (model_type, subgroups) in enumerate(groups.items()):
            color = colors[i % len(colors)]
            # 计算大类的总数（可选，用于排序或视觉）
            total = sum(item['value'] for item in subgroups)
            # 每个大类节点
            group_node = {
                'name': model_type,
                'children': subgroups,
                'itemStyle': {
                    'color': color   # 大类节点颜色，但通常不显示，可通过 level 控制
                }
            }
            # 为每个子节点也分配相同的颜色（确保第二层使用）
            for subgroup in group_node['children']:
                subgroup['itemStyle'] = {'color': color}
            treemap_data.append(group_node)

        return jsonify(treemap_data)

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/variable-percent-stack')
def variable_percent_stack():
    """
    返回模型变量百分比堆叠柱状图数据。
    纵轴：模型类型 (model_type)
    横轴：百分比 (0-100%)
    系列：8种变量类型，分别对应以下字段（均为 INTEGER 类型，存储变量个数）：
        - Baseline: patient_baseline_characteristics
        - Preoperative: preoperative
        - Imaging: imaging_tumor
        - Surgical anesthetic: surgical_anesthetic
        - Intraoperative: intraoperative
        - Postoperative: early_postoperative
        - Risk score: risk_scores
        - Unclassified: unclassified
    """
    db = get_db()
    try:
        var_fields = [
            ('Baseline', 'patient_baseline_characteristics'),
            ('Preoperative', 'preoperative'),
            ('Imaging', 'imaging_tumor'),
            ('Surgical anesthetic', 'surgical_anesthetic'),
            ('Intraoperative', 'intraoperative'),
            ('Postoperative', 'early_postoperative'),
            ('Risk score', 'risk_scores'),
            ('Unclassified', 'unclassified')
        ]

        columns = [field for _, field in var_fields]
        # 移除 ORDER BY model_type，后续按总数排序
        query = f"""
        SELECT model_type, {', '.join(columns)}
        FROM development
        WHERE model_type IS NOT NULL AND model_type != ''
        """
        rows = db.execute(query).fetchall()

        if not rows:
            return jsonify({'error': 'No data found'}), 404

        # 辅助函数：直接返回整数值（兼容 None 和字符串）
        def get_count(value):
            if value is None:
                return 0
            if isinstance(value, int):
                return value
            try:
                return int(value)  # 若存储为字符串，尝试转换
            except (ValueError, TypeError):
                return 0

        from collections import defaultdict
        agg = defaultdict(lambda: defaultdict(int))
        model_types_set = set()

        for row in rows:
            mt = row['model_type']
            model_types_set.add(mt)
            for var_name, field in var_fields:
                value = row[field] if field in row.keys() else None
                cnt = get_count(value)
                agg[mt][var_name] += cnt

        # 按每个 model_type 的总变量数降序排序（总数多的排在前面）
        model_types = sorted(model_types_set, key=lambda mt: sum(agg[mt].values()), reverse=False)

        series_data = {var_name: [] for var_name, _ in var_fields}

        for mt in model_types:
            total = sum(agg[mt].values())
            if total == 0:
                for var_name, _ in var_fields:
                    series_data[var_name].append(0)
            else:
                for var_name, _ in var_fields:
                    cnt = agg[mt][var_name]
                    percent = (cnt / total) * 100
                    series_data[var_name].append(round(percent, 2))

        series_list = []
        for var_name, _ in var_fields:
            series_list.append({
                'name': var_name,
                'type': 'bar',
                'stack': 'percent',
                'data': series_data[var_name]
            })

        return jsonify({
            'model_types': model_types,
            'series': series_list
        })

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()

@bp.route('/chart/evidence-quality')
def evidence_quality():
    """返回证据质量堆叠柱状图绝对数量数据"""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT categories, score
            FROM development
            WHERE categories IS NOT NULL AND categories != ''
              AND score IS NOT NULL
        """).fetchall()
        if not rows:
            return jsonify({'error': 'No evidence quality data found'}), 404

        # 字母到全称的映射
        letter_to_full = {'H': 'High', 'L': 'Low', 'U': 'Unclear'}
        # 分数段定义：名称、范围、颜色（柔和版）
        score_ranges = [
            ('Excellent', (11, 13), '#F5CBD8'),   # 柔和红
            ('Good', (8, 10), '#E9D9F3'),         # 柔和蓝
            ('Fair', (4, 7), '#F8E0C5'),           # 柔和绿
            ('Poor', (0, 3), '#E4F0CB')            # 浅黄
        ]

        from collections import defaultdict
        category_counts = defaultdict(lambda: {r[0]: 0 for r in score_ranges})

        for row in rows:
            cat = row['categories']
            score = row['score']
            parts = cat.split('-')
            if len(parts) != 2:
                continue
            full_parts = [letter_to_full.get(p, p) for p in parts]
            full_cat = '-'.join(full_parts)

            for range_name, (low, high), _ in score_ranges:
                if low <= score <= high:
                    category_counts[full_cat][range_name] += 1
                    break

        if not category_counts:
            return jsonify({'error': 'No valid category data'}), 404

        # 排序函数：先按第一部分优先级，再按第二部分
        # 确保 High-High 排在最前面
        def category_key(cat):
            parts = cat.split('-')
            order = {'High': 1, 'Low': 3, 'Unclear': 2}
            return (order.get(parts[0], 4), order.get(parts[1], 4))
        categories = sorted(category_counts.keys(), key=category_key)

        # 构建系列数据（绝对数量）
        series = []
        for range_name, _, color in score_ranges:
            data = [category_counts[cat][range_name] for cat in categories]
            series.append({
                'name': range_name,
                'type': 'bar',
                'stack': 'quality',
                'data': data,
                'itemStyle': {'color': color}
            })

        return jsonify({
            'categories': categories,
            'series': series
        })

    except Exception as e:
        return jsonify(error=f"Database Error: {str(e)}"), 500
    finally:
        if db:
            db.close()