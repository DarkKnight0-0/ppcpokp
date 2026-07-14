// comparison.js

let allData = [];               // 原始数据
let filteredData = [];          // 当前筛选后的数据（用于分页）
let currentPage = 1;
const itemsPerPage = 6;
let selectedModels = [];        // 已选模型 { model_id, model_name }

// 页面加载完成后初始化
$(document).ready(function () {
    // 绑定检索按钮
    $('#searchBtn').on('click', function () {
        loadData();
    });

    // 绑定重置按钮
    $('#resetBtn').on('click', function () {
        resetForm();
    });

    // 绑定比较按钮
    $('#compareBtn').on('click', function () {
        compareModels();
    });

    // 初始加载（可选）
    // loadData();
});

// 获取表单参数
function getFilterParams() {
    const params = new URLSearchParams();

    // 文本输入
    $('input[name="pmid"]').val() && params.append('pmid', $('input[name="pmid"]').val());
    $('input[name="model_name"]').val() && params.append('model_name', $('input[name="model_name"]').val());
    $('input[name="model_id"]').val() && params.append('model_id', $('input[name="model_id"]').val());

    // 多选：population_category
    $('input[name="population_category"]:checked').each(function () {
        params.append('population_category', $(this).val());
    });

    // 多选：surgery_discipline
    $('input[name="surgery_discipline"]:checked').each(function () {
        params.append('surgery_discipline', $(this).val());
    });

    // 多选：target_outcome
    $('input[name="target_outcome"]:checked').each(function () {
        params.append('target_outcome', $(this).val());
    });

    // 多选：timing_prediction
    $('input[name="timing_prediction"]:checked').each(function () {
        params.append('timing_prediction', $(this).val());
    });

    // 多选：variable_number_range
    $('input[name="variable_number_range"]:checked').each(function () {
        params.append('variable_number_range', $(this).val());
    });

    // 多选：application_modality
    $('input[name="application_modality"]:checked').each(function () {
        params.append('application_modality', $(this).val());
    });

    return params;
}

// 加载数据
async function loadData() {
    const params = getFilterParams();
    const url = `/tool/comparison-data?${params.toString()}`;

    $('#loading').show();
    $('#data-container').empty();
    $('#no-results').hide();

    try {
        const response = await fetch(url);
        const result = await response.json();
        if (result.rows) {
            allData = result.rows;
            filteredData = [...allData];
            $('#resultCount').text(filteredData.length);
            if (filteredData.length === 0) {
                showNoResults();
            } else {
                currentPage = 1;
                renderPage(currentPage);
                renderPagination();
                updatePaginationInfo();
            }
        } else {
            showNoResults();
        }
    } catch (error) {
        console.error('加载失败', error);
        showNoResults();
    } finally {
        $('#loading').hide();
    }
}

// 渲染卡片
function renderPage(page) {
    const container = $('#data-container');
    container.empty();

    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageData = filteredData.slice(start, end);

    pageData.forEach(item => {
        const card = createCard(item);
        container.append(card);
        // 初始化雷达图
        setTimeout(() => {
            initRadarChart(`chart-${item.model_id}`, item, scoreToLevel(item.score));
        }, 50);
    });
}

// 创建卡片 HTML
function createCard(item) {
    const level = scoreToLevel(item.score);
    const logo = modelTypeToLogo(item.model_type);
    const col = $('<div>').addClass('col-12 col-xl-6 py-2');
    col.html(`
        <div class="card h-100">
            <div class="card-header-${level}">
                <h5 class="card-title mt-2 clickable-title text-truncate" style="cursor: pointer;" data-model-id="${item.model_id}" onclick="showDetail(this.dataset.modelId)">${item.model_name}</h5>
                <span class="model-id text-nowrap ms-2">${item.model_id}</span>
                <span class="icon icon-${logo} icon--36"></span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-7">
                        <h6 class="card-title text-center">Model Score System</h6>
                        <div class="chart-container" id="chart-${item.model_id}"></div>
                    </div>
                    <div class="col-md-5">
                        <h6 class="card-title text-center">Model Preview</h6>
                        <table class="table table-striped profile-table table-${level}">
                            <tbody>
                                <tr><th class="align-middle text-center">AUC</th><td class="align-middle text-center">${item.auc0 || 'N/A'}</td></tr>
                                <tr><th class="align-middle text-center">Sensitivity</th><td class="align-middle text-center">${item.sensitivity0 || 'N/A'}</td></tr>
                                <tr><th class="align-middle text-center">Specificity</th><td class="align-middle text-center">${item.specificity0 || 'N/A'}</td></tr>
                                <tr><th class="align-middle text-center">Calibration</th><td class="align-middle text-center">${item.calibration0 || 'N/A'}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="col-12 mt-3">
                        <b>Total Score: ${item.score || 'N/A'}/13</b> | Study Setting: ${item.study_setting || 'N/A'} | Sample Size: ${item.sample_size_score || 'N/A'} | Discrimination (AUC): ${item.discrimination || 'N/A'} | Calibration: ${item.calibration || 'N/A'} | Validation: ${item.validation || 'N/A'} | Clinical Usability: ${item.clinical_usability || 'N/A'}
                        <hr>
                        <p class="authors-text text-truncate">AU: ${item.authors || 'N/A'}</p>
                    </div>
                </div>
            </div>
            <div class="card-footer bg-white border-top-0 pb-2">
                <button class="btn btn-outline-primary btn-sm btn-add" data-model-id="${item.model_id}" data-model-name="${item.model_name}">Add to Selection</button>
            </div>
        </div>
    `);
    // 绑定添加事件
    col.find('.btn-add').on('click', function () {
        addToSelection(item);  // item 即为当前卡片的完整数据对象
    });
    return col;
}

// 分数转等级（复用 development.js）
function scoreToLevel(score) {
    if (score >= 11) return 'excellent';
    if (score >= 8) return 'good';
    if (score >= 4) return 'fair';
    return 'poor';
}

function modelTypeToLogo(type) {
    if (type == 'Traditional Statistical Model') return '2';
    if (type == 'Multi-Model / Hybrid Learning Strategy') return '3';
    if (type == 'Unclassified Method') return '4';
    return '1';
}

// 雷达图初始化（复制自 development.js，略作调整）
function initRadarChart(containerId, item, level) {
    const chartDom = document.getElementById(containerId);
    if (!chartDom) return;
    const myChart = echarts.init(chartDom);
    const indicators = [
        { name: 'Study\ndesign', max: 1 },
        { name: 'Study\nsetting', max: 2 },
        { name: 'Sample\nsize', max: 2 },
        { name: 'Discrimination\n(AUC)', max: 2 },
        { name: 'Calibration', max: 2 },
        { name: 'Validation', max: 2 },
        { name: 'Clinical\nusability', max: 2 }
    ];
    const dataValues = [
        item.study_design || 0,
        item.study_setting || 0,
        item.sample_size_score || 0,
        item.discrimination || 0,
        item.calibration || 0,
        item.validation || 0,
        item.clinical_usability || 0
    ];

    let areaColor, lineColor;
    switch (level.toLowerCase()) {
        case 'excellent':
            areaColor = 'rgba(245, 203, 216, 0.7)';
            lineColor = '#E91E63';
            break;
        case 'good':
            areaColor = 'rgba(233, 217, 243, 0.7)';
            lineColor = '#9C27B0';
            break;
        case 'fair':
            areaColor = 'rgba(248, 224, 197, 0.7)';
            lineColor = '#FF9800';
            break;
        default:
            areaColor = 'rgba(228, 240, 203, 0.7)';
            lineColor = '#8BC34A';
    }

    const option = {
        tooltip: { trigger: 'item' },
        radar: {
            indicator: indicators,
            shape: 'circle',
            radius: '51%',
            center: ['50%', '50%'],
            splitNumber: 3,
            axisName: { color: '#666', fontSize: 10, fontWeight: 'bold', lineHeight: 14 },
            nameGap: 15,
            splitArea: { areaStyle: { color: ['rgba(52,152,219,0.1)', 'rgba(52,152,219,0.05)', 'rgba(52,152,219,0.02)'] } },
            axisLine: { lineStyle: { color: 'rgba(52,152,219,0.3)' } },
            splitLine: { lineStyle: { color: 'rgba(52,152,219,0.3)' } }
        },
        series: [{
            type: 'radar',
            data: [{
                value: dataValues,
                name: 'Score',
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: lineColor },
                areaStyle: { color: areaColor },
                itemStyle: { color: lineColor }
            }]
        }],
        grid: { top: 5, bottom: 5, left: 5, right: 5 }
    };
    myChart.setOption(option);
    $(window).on('resize', () => myChart.resize());
}

// 分页渲染
function renderPagination() {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const pagination = $('#bootstrap-pagination');
    pagination.empty();
    if (totalPages <= 1) return;

    let html = '';
    // 上一页
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}"><a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;"><i class="bi bi-chevron-left"></i></a></li>`;

    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, currentPage + 2);
    if (end - start < 4) {
        if (start === 1) end = Math.min(totalPages, start + 4);
        else if (end === totalPages) start = Math.max(1, end - 4);
    }

    if (start > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1); return false;">1</a></li>`;
        if (start > 2) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a></li>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a></li>`;
    }

    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}"><a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;"><i class="bi bi-chevron-right"></i></a></li>`;
    pagination.html(html);
}

function changePage(page) {
    currentPage = page;
    renderPage(currentPage);
    renderPagination();
    updatePaginationInfo();
    $('html, body').animate({ scrollTop: $('#results-section').offset().top }, 300);
}

function updatePaginationInfo() {
    const total = filteredData.length;
    const start = (currentPage - 1) * itemsPerPage + 1;
    const end = Math.min(currentPage * itemsPerPage, total);
    $('#pagination-info').text(`Showing ${start} to ${end} of ${total} rows`);
}

function showNoResults() {
    $('#no-results').show();
    $('#data-container').empty();
    $('#bootstrap-pagination').empty();
    $('#pagination-info').text('Showing 0 to 0 of 0 rows');
}

// 备选库管理
function addToSelection(model) {   // model 是完整的模型对象
    if (selectedModels.length >= 6) {
        alert('You can select at most 6 models for comparison.');
        return;
    }
    if (selectedModels.find(m => m.model_id === model.model_id)) {
        alert('This model is already in the selection.');
        return;
    }
    selectedModels.push(model);
    renderSelectedList();
}

function removeFromSelection(modelId) {
    selectedModels = selectedModels.filter(m => m.model_id !== modelId);
    renderSelectedList();
}

function renderSelectedList() {
    const container = $('#selectedModelsList');
    container.empty();
    if (selectedModels.length === 0) {
        container.html('<p class="text-muted text-center">No models selected.</p>');
        $('#compareBtn').prop('disabled', true);
    } else {
        selectedModels.forEach(m => {
            // 根据分数获取等级和背景色
            const level = scoreToLevel(m.score || 0);        // 可使用 tool_comparison.js 中已有的 scoreToLevel
            const colors = getColorByLevel(level);           // 来自 common.js
            const bgColor = colors.area;                      // 例如 "rgba(245, 203, 216, 0.5)"

            // 处理作者和期刊截断
            const authors = m.authors 
                ? (m.authors.length > 30 ? m.authors.substring(0, 27) + '...' : m.authors) 
                : 'N/A';
            const journal = m.journal_name 
                ? (m.journal_name.length > 20 ? m.journal_name.substring(0, 17) + '...' : m.journal_name) 
                : 'N/A';

            const itemDiv = $(`
                <div class="selected-model-item" style="background-color: ${bgColor};">
                    <div class="model-info">
                        <strong>${m.model_id}</strong> - ${m.model_name}<br>
                        <small>${authors} | ${journal}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeFromSelection('${m.model_id}')">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            `);
            container.append(itemDiv);
        });
        $('#compareBtn').prop('disabled', false);
    }
    $('#selectedCount').text(selectedModels.length);
}

function compareModels() {
    if (selectedModels.length === 0 || selectedModels.length > 6) return;
    const ids = selectedModels.map(m => m.model_id).join('&model_id=');
    window.location.href = `/tool/comparison_result?model_id=${ids}`;
}

// 重置表单
function resetForm() {
    $('#comparisonForm')[0].reset();  // 仅重置表单输入
    loadData();                       // 重新加载无筛选数据，右侧备选框保持不变
}

// 为简单起见，将 changePage, removeFromSelection 暴露为全局
window.changePage = changePage;
window.removeFromSelection = removeFromSelection;
// 如果需要详情模态框，可以复制 development.js 中的 showDetail 函数，但此处省略