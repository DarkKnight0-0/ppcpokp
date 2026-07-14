
// 全局变量
let allData = [];
let currentPage = 1;
const itemsPerPage = 6;
let filteredData = [];
let searchTimeout;

// 应用URL参数
function applyUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);

    // 设置模型名称
    const urlModelName = urlParams.get('model_name');
    if (urlModelName) {
        $('#model_name').val(urlModelName);
    }

    // 设置目标结果
    const target_outcomes = urlParams.getAll('target_outcome');
    // 取消所有复选框的选中状态
    $('input[name="target_outcome"]').prop('checked', false);
    // 根据URL参数选中对应的复选框
    target_outcomes.forEach(type => {
        $(`input[name="target_outcome"][value="${type}"]`).prop('checked', true);
    });

    // 设置模型类型复选框
    const modelTypes = urlParams.getAll('model_type');
    // 取消所有复选框的选中状态
    $('input[name="model_type"]').prop('checked', false);
    // 根据URL参数选中对应的复选框
    modelTypes.forEach(type => {
        $(`input[name="model_type"][value="${type}"]`).prop('checked', true);
    });

    // 设置预测时机
    const timingPrediction = urlParams.get('timing_prediction');
    if (timingPrediction) {
        $('#timing_prediction').val(timingPrediction);
    }

    // 设置应用方式复选框
    const applicationModalities = urlParams.getAll('application_modality');
    // 取消所有复选框的选中状态
    $('input[name="application_modality"]').prop('checked', false);
    // 根据URL参数选中对应的复选框
    applicationModalities.forEach(type => {
        $(`input[name="application_modality"][value="${type}"]`).prop('checked', true);
    });

    // 设置效用复选框
    const utilityTypes = ['excellent', 'good', 'fair', 'poor'];
    utilityTypes.forEach(type => {
        if (urlParams.get(type) === 'true') {
            $(`#${type}`).prop('checked', true);
        }
    });

    // 设置整体质量
    const overallQuality = urlParams.get('overallQuality');
    if (overallQuality) {
        $('#overallQuality').val(overallQuality);
    }

    // 设置整体适用性
    const overallApplicability = urlParams.get('overallApplicability');
    if (overallApplicability) {
        $('#overallApplicability').val(overallApplicability);
    }

    // 设置年份范围
    const urlMinYear = urlParams.get('minYear');
    if (urlMinYear) {
        const slider = document.getElementById('yearRangeSlider');
        slider.noUiSlider.set([parseInt(urlMinYear), null]);
    }

    const urlMaxYear = urlParams.get('maxYear');
    if (urlMaxYear) {
        const slider = document.getElementById('yearRangeSlider');
        slider.noUiSlider.set([null, parseInt(urlMaxYear)]);
    }

    getData(urlParams);
}

// 加载数据

// loadData函数
async function loadData() {
    // 获取筛选参数
    const filterParams = getFilterParams();

    // 构建查询参数
    const queryParams = new URLSearchParams();

    Object.entries(filterParams).forEach(([key, value]) => {
        if (value === null || value === undefined || value === '' || value === 'any') {
            return; // 跳过空值
        }

        if (Array.isArray(value)) {
            // 数组：添加多个同名参数
            value.filter(item => item && item !== '').forEach(item => {
                queryParams.append(key, item);
            });
        } else {
            // 非数组：添加单个参数
            queryParams.append(key, value);
        }
    });

    getData(queryParams);
}

async function getData(queryParams) {
    try {
        // 显示加载状态
        document.getElementById('loading').style.display = 'block';
        document.getElementById('data-container').innerHTML = '';

        // 获取数据（包含筛选参数）
        const url = `/browse/development-data?${queryParams.toString()}`;
        const response = await fetch(url);
        const result = await response.json();

        // 检查数据格式
        if (result.rows && Array.isArray(result.rows)) {
            allData = result.rows;
            filteredData = [...allData];

            // 应用文本搜索
            const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
            if (searchTerm !== '') {
                filteredData = filteredData.filter(item => {
                    return (
                        (item.model_name && item.model_name.toLowerCase().includes(searchTerm)) ||
                        (item.title && item.title.toLowerCase().includes(searchTerm)) ||
                        (item.authors && item.authors.toLowerCase().includes(searchTerm)) ||
                        (item.journal_name && item.journal_name.toLowerCase().includes(searchTerm)) ||
                        (item.conclusion && item.conclusion.toLowerCase().includes(searchTerm))
                    );
                });
            }

            // 重置到第一页
            currentPage = 1;

            // 更新UI
            renderPage(currentPage);
            renderBootstrapPagination();
            updatePaginationInfo()
        } else {
            console.error('数据格式错误:', result);
            showNoResults();
        }

        // 隐藏加载状态
        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('loading').style.display = 'none';
        showNoResults();
    }
}

// 设置事件监听器
function setupEventListeners() {

    // 搜索框输入即时搜索（防抖处理）

    document.getElementById('search-input').addEventListener('input', function (event) {

        clearTimeout(searchTimeout);

        searchTimeout = setTimeout(() => {

            performSearch();

        }, 300);

    });

    // 筛选表单变化事件
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('change', function () {
            performSearch();
        });
    }

    // 搜索框回车事件
    document.getElementById('search-input').addEventListener('keyup', function (event) {

        if (event.key === 'Enter') {

            performSearch();

        }

    });

}

// 执行搜索
function performSearch() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();

    // 首先应用侧边栏筛选
    let tempFiltered = [...allData];

    // 应用文本搜索
    if (searchTerm !== '') {
        tempFiltered = tempFiltered.filter(item => {
            return (
                (item.model_name && item.model_name.toLowerCase().includes(searchTerm)) ||
                (item.title && item.title.toLowerCase().includes(searchTerm)) ||
                (item.model_id && item.model_id.toLowerCase().includes(searchTerm))
            );
        });
    }

    // 应用筛选条件
    tempFiltered = applyFilters(tempFiltered);
    filteredData = tempFiltered;
    currentPage = 1;

    renderPage(currentPage);
    renderBootstrapPagination();
    updatePaginationInfo();

}

// 应用筛选条件
function applyFilters(data) {
    let filtered = [...data];
    // 这里可以添加更多的筛选逻辑
    // 例如：年份范围、模型类型等
    return filtered;
}

// 渲染当前页数据
function renderPage(page) {

    currentPage = page;

    const container = document.getElementById('data-container');

    container.innerHTML = '';



    const startIndex = (page - 1) * itemsPerPage;

    const endIndex = startIndex + itemsPerPage;

    const pageData = filteredData.slice(startIndex, endIndex);



    if (pageData.length === 0) {

        showNoResults();

        return;

    }



    // 隐藏无结果提示
    document.getElementById('no-results').style.display = 'none';



    pageData.forEach((item, index) => {

        const card = createCard(item, startIndex + index + 1);

        container.appendChild(card);



        setTimeout(() => {

            initRadarChart(`chart-${item.model_id}`, item, `${scoreToLevel(item.score)}`);

        }, 100);

    });

}

//分数转为等级
function scoreToLevel(score) {

    if (score >= 11) return 'excellent';

    if (score >= 8) return 'good';

    if (score >= 4) return 'fair';

    return 'poor';

}

// 模型类型转为图标编号
function modelTypeToLogo(type) {
    if (type == 'Traditional Statistical Model') return '2';
    if (type == 'Multi-Model / Hybrid Learning Strategy') return '3';
    if (type == 'Unclassified Method') return '4';
    return '1';
}

// 创建卡片HTML
function createCard(item, displayIndex) {

    const col = document.createElement('div');
    col.className = 'col-12 col-xl-6 py-2';
    col.innerHTML = `
                <div class="card h-100">
                    <div class="card-header-${scoreToLevel(item.score)}">
                        <h5 class="card-title mt-2 clickable-title text-truncate" style="cursor: pointer;" data-model-id="${item.model_id}" onclick="showDetail(this.dataset.modelId)">${item.model_name}</h5>
                        <span class="model-id text-nowrap ms-2">${item.model_id}</span>
                        <span class="icon icon-${modelTypeToLogo(item.model_type)} icon--36"></span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-7">
                                <h6 class="card-title text-center">Model Score System</h6>
                                <div class="chart-container" id="chart-${item.model_id}"></div>
                            </div>
                            <div class="col-md-5">
                                <h6 class="card-title text-center">Model Preview</h6>
                                <table class="table table-striped profile-table table-${scoreToLevel(item.score)}">
                                    <tbody>
                                        <tr>
                                            <th class="align-middle text-center">AUC</th>
                                            <td class="align-middle text-center">${item.auc0 || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="align-middle text-center">Sensitivity</th>
                                            <td class="align-middle text-center">${item.sensitivity0 || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="align-middle text-center">Specificity</th>
                                            <td class="align-middle text-center">${item.specificity0 || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th class="align-middle text-center">Calibration</th>
                                            <td class="align-middle text-center">${item.calibration0 || 'N/A'}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div class="col-12 mt-3">
                                <b>Total Score: ${item.score || 'N/A'}/13</b> | Study Setting:
                                ${item.study_setting || 'N/A'} | Sample Size: ${item.sample_size_score || 'N/A'} | Discrimination
                                (AUC): ${item.discrimination || 'N/A'} | Calibration: ${item.calibration || 'N/A'} | Validation:
                                ${item.validation || 'N/A'} | Clinical Usability: ${item.clinical_usability || 'N/A'}
                                <hr>
                                <p class="authors-text text-truncate">AU: ${item.authors || 'N/A'}</p>
                        </div>
                    </div>
                </div>
            `;

    return col;
}

// Bootstrap Table 样式分页
function renderBootstrapPagination() {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const paginationEl = document.getElementById('bootstrap-pagination');

    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }

    let paginationHTML = '';

    // 上一页
    paginationHTML += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" ${currentPage !== 1 ? `onclick="changePage(${currentPage - 1}); return false;"` : ''}>
                    <i class="bi bi-chevron-left"></i>
                </a>
            </li>
        `;



    // 计算显示的页码
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (endPage - startPage < 4) {
        if (startPage === 1) {
            endPage = Math.min(totalPages, startPage + 4);
        } else if (endPage === totalPages) {
            startPage = Math.max(1, endPage - 4);
        }
    }

    // 第一页
    if (startPage > 1) {
        paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="changePage(1); return false;">1</a>
                </li>
            `;

        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }



    // 中间页码

    for (let i = startPage; i <= endPage; i++) {

        paginationHTML += `

                <li class="page-item ${i === currentPage ? 'active' : ''}">

                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>

                </li>

            `;

    }



    // 最后一页

    if (endPage < totalPages) {

        if (endPage < totalPages - 1) {

            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;

        }

        paginationHTML += `

                <li class="page-item">

                    <a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a>

                </li>

            `;

    }



    // 下一页

    paginationHTML += `

            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">

                <a class="page-link" href="#" ${currentPage !== totalPages ? `onclick="changePage(${currentPage + 1}); return false;"` : ''}>

                    <i class="bi bi-chevron-right"></i>

                </a>

            </li>

        `;



    paginationEl.innerHTML = paginationHTML;

}

// 切换页面
function changePage(page) {

    currentPage = page;

    renderPage(page);

    renderBootstrapPagination();

    updatePaginationInfo();



    // 滚动到顶部

    window.scrollTo({ top: 0, behavior: 'smooth' });

}

// 更新分页信息
function updatePaginationInfo() {

    const totalItems = filteredData.length;

    const startIndex = (currentPage - 1) * itemsPerPage + 1;

    const endIndex = Math.min(currentPage * itemsPerPage, totalItems);



    document.getElementById('pagination-info').textContent =

        `Showing ${startIndex} to ${endIndex} of ${totalItems} rows`;

}

// 显示加载状态
function showLoading() {

    document.getElementById('loading').style.display = 'block';

    document.getElementById('no-results').style.display = 'none';

}

// 隐藏加载状态
function hideLoading() {

    document.getElementById('loading').style.display = 'none';

}

// 显示无结果
function showNoResults() {

    document.getElementById('no-results').style.display = 'block';

    document.getElementById('data-container').innerHTML = '';

    document.getElementById('bootstrap-pagination').innerHTML = '';

    document.getElementById('pagination-info').textContent = 'Showing 0 to 0 of 0 rows';

}

// 雷达图初始化
function initRadarChart(containerId, item, level) {
    const chartDom = document.getElementById(containerId);

    if (!chartDom) return;

    const myChart = echarts.init(chartDom);
    const indicators = [
        { name: 'Study\ndesign', max: 1 },          // 手动换行
        { name: 'Study\nsetting', max: 2 },        // 手动换行
        { name: 'Sample\nsize', max: 2 },          // 手动换行
        { name: 'Discrimination\n(AUC)', max: 2 }, // 手动换行
        { name: 'Calibration', max: 2 },
        { name: 'Validation', max: 2 },
        { name: 'Clinical\nusability', max: 2 }    // 手动换行
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

    // 根据level设置颜色
    let areaColor, lineColor;
    switch (level.toLowerCase()) {
        case 'excellent':
            areaColor = 'rgba(245, 203, 216, 0.7)'; // #F5CBD8 透明度0.7
            lineColor = '#E91E63'; // 粉红色系的深色
            break;
        case 'good':
            areaColor = 'rgba(233, 217, 243, 0.7)'; // #E9D9F3 透明度0.7
            lineColor = '#9C27B0'; // 紫色系的深色
            break;
        case 'fair':
            areaColor = 'rgba(248, 224, 197, 0.7)'; // #F8E0C5 透明度0.7
            lineColor = '#FF9800'; // 橙色系的深色
            break;
        case 'poor':
            areaColor = 'rgba(228, 240, 203, 0.7)'; // #E4F0CB 透明度0.
            lineColor = '#8BC34A'; // 绿色系的深色
            break;
        default:
            areaColor = 'rgba(52, 152, 219, 0.3)';
            lineColor = '#3498db';
    }

    const option = {
        tooltip: {
            trigger: 'item'
        },
        radar: {
            indicator: indicators,
            shape: 'circle',
            radius: '51%', // 减小半径，给标签更多空间
            center: ['50%', '50%'], // 确保居中
            splitNumber: 3,
            axisName: {
                color: '#666',
                fontSize: 10, // 减小字体大小
                fontWeight: 'bold',
                lineHeight: 14// 设置行高

            },
            nameGap: 15, // 调整标签与雷达图的距离
            // 调整标签位置
            axisNameGap: 8,
            // 设置标签位置偏移
            axisLabel: {
                margin: 3
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(52, 152, 219, 0.1)', 'rgba(52, 152, 219, 0.05)', 'rgba(52, 152, 219, 0.02)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(52, 152, 219, 0.3)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(52, 152, 219, 0.3)'
                }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: dataValues,
                name: 'Score',
                symbol: 'circle',
                symbolSize: 6, // 减小符号大小
                lineStyle: {
                    width: 2, // 减小线宽
                    color: lineColor
                },
                areaStyle: {
                    color: areaColor
                },
                itemStyle: {
                    color: lineColor
                }
            }]
        }],
        grid: {
            top: 5,
            bottom: 5,
            left: 5,
            right: 5
        }
    };

    myChart.setOption(option);
    window.addEventListener('resize', function () {
        myChart.resize();
    });
}

// 初始化 noUiSlider
function initNoUiSlider() {

    const currentYear = new Date().getFullYear();

    const minYear = 1994;



    const slider = document.getElementById('yearRangeSlider');

    const minYearInput = document.getElementById('minYearInput');

    const maxYearInput = document.getElementById('maxYearInput');



    if (!slider) return;



    if (slider.noUiSlider) {

        slider.noUiSlider.destroy();

    }



    window.yearSlider = noUiSlider.create(slider, {

        start: [minYear, currentYear],

        connect: true,

        step: 1,

        range: {

            'min': minYear,

            'max': currentYear

        },

        pips: {

            mode: 'values',

            values: [1994, 2000, 2005, 2010, 2015, 2020, currentYear],

            density: 4,

            format: {

                to: function (value) {

                    return Math.round(value);

                }

            }

        }

    });



    window.yearSlider.on('update', function (values) {

        const minYearSelected = Math.floor(parseFloat(values[0]));

        const maxYearSelected = Math.floor(parseFloat(values[1]));



        if (minYearInput) minYearInput.value = minYearSelected;

        if (maxYearInput) maxYearInput.value = maxYearSelected;

    });



    window.yearSlider.on('change', function (values) {

        loadData();

    });

}

// 获取表单筛选参数
function getFilterParams() {
    // 读取URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const urlModelName = urlParams.get('model_name');

    // 获取选中的目标结果（多选）
    const target_outcomes = [];
    $('input[name="target_outcome"]:checked').each(function () {
        target_outcomes.push($(this).val());
    });

    // 获取选中的模型类型（多选）
    const modelTypes = [];
    $('input[name="model_type"]:checked').each(function () {
        modelTypes.push($(this).val());
    });

    // 获取选中的应用方式（多选）
    const applicationModalities = [];
    $('input[name="application_modality"]:checked').each(function () {
        applicationModalities.push($(this).val());
    });

    return {
        model_name: $('#model_name').val() || '',
        minYear: $('#minYearInput').val() || '',
        maxYear: $('#maxYearInput').val() || '',
        target_outcome: target_outcomes,
        model_type: modelTypes,
        timing_prediction: $('#timing_prediction').val() || 'any',
        application_modality: applicationModalities,

        excellent: $('#excellent').is(':checked') ? 'true' : '',

        good: $('#good').is(':checked') ? 'true' : '',

        fair: $('#fair').is(':checked') ? 'true' : '',

        poor: $('#poor').is(':checked') ? 'true' : '',

        overallQuality: $('#overallQuality').val(),

        overallApplicability: $('#overallApplicability').val()

    };

}


// 重置筛选条件
function resetFilters() {
    $('#model_name').val('');
    $('input[name="target_outcome"]').prop('checked', false);
    $('input[name="model_type"]').prop('checked', false);
    $('#timing_prediction').val('any');
    $('input[name="application_modality"]').prop('checked', false);

    $('#excellent').prop('checked', false);

    $('#good').prop('checked', false);

    $('#fair').prop('checked', false);

    $('#poor').prop('checked', false);

    $('#overallQuality').val('any');

    $('#overallApplicability').val('any');

    $('#search-input').val('');



    const currentYear = new Date().getFullYear();

    if (window.yearSlider) {

        window.yearSlider.set([1994, currentYear]);

    }



    loadData();

}

// 模态框相关函数
function showDetail(id) {
    console.log("Loading detail for ID:", id);

    // 清空之前的内容
    const iframeContainer = document.getElementById('iframe-container');
    iframeContainer.innerHTML = '';

    // 创建loading状态
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'd-flex justify-content-center align-items-center h-100 w-100';
    loadingDiv.style.minHeight = '400px';
    loadingDiv.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading detail...</p>
        </div>
    `;
    iframeContainer.appendChild(loadingDiv);

    // 设置模态框标题
    document.getElementById('detailModalLabel').textContent = `Model Detail - ${id}`;

    // 显示模态框
    const modalElement = document.getElementById('detailModal');
    const modal = new bootstrap.Modal(modalElement, {
        backdrop: true,
        keyboard: true
    });

    modal.show();

    // 延迟创建iframe，确保模态框完全显示
    setTimeout(() => {
        // 创建iframe
        const iframe = document.createElement('iframe');
        iframe.id = 'detail-iframe';
        iframe.src = `/browse/development-detail?id=${id}`; // 注意：需要一个完整页面的路由
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.style.minHeight = '500px';

        // 监听iframe加载完成
        iframe.onload = function () {
            console.log('iframe loaded');

            // 调整iframe高度以适应内容
            try {
                // 注意：同源才能访问iframe内容
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const bodyHeight = iframeDoc.body.scrollHeight;
                const htmlHeight = iframeDoc.documentElement.scrollHeight;
                const height = Math.max(bodyHeight, htmlHeight, 500);

                iframe.style.height = height + 'px';

                // 更新模态框标题（如果iframe页面有标题）
                const iframeTitle = iframeDoc.title ||
                    iframeDoc.querySelector('h1, h2, .detail-title')?.textContent;
                if (iframeTitle) {
                    document.getElementById('detailModalLabel').textContent =
                        iframeTitle.length > 50 ? iframeTitle.substring(0, 50) + '...' : iframeTitle;
                }
            } catch (e) {
                // 跨域安全限制，无法访问iframe内部
                console.warn('Error:', e);
            }
        };

        // 处理iframe加载错误
        iframe.onerror = function () {
            iframeContainer.innerHTML = `
                <div class="d-flex justify-content-center align-items-center h-100 w-100">
                    <div class="alert alert-danger w-75 text-center">
                        Failed to load detail. Please try again.
                    </div>
                </div>
            `;
        };

        // 清空容器并添加iframe
        iframeContainer.innerHTML = '';
        iframeContainer.appendChild(iframe);

    }, 100);
}

// 在 development.html 的脚本中添加
// 监听iframe发来的消息，调整iframe高度
window.addEventListener('message', function (event) {
    if (event.data.type === 'iframe-resize') {
        const iframe = document.getElementById('detail-iframe');
        if (iframe) {
            iframe.style.height = event.data.height + 'px';
        }
    }
});

// 页面加载完成后初始化
$(document).ready(function () {
    if (document.getElementById('yearRangeSlider')) {
        initNoUiSlider();
    }

    // 从URL获取参数
    applyUrlParams();

    setupEventListeners();

    // 绑定筛选表单的change事件
    $('#filterForm').on('change', 'input[type="checkbox"], select', function (e) {
        if ($(this).is('input[type="text"]')) {
            return;
        }
        loadData();
    });

    // 模型名称输入框防抖处理
    $('#model_name').on('input', function () {
        clearTimeout(window.modelNameTimeout);
        window.modelNameTimeout = setTimeout(() => {
            loadData();
        }, 300);
    });

    // 绑定模态框事件
    const modalElement = document.getElementById('detailModal');
    if (modalElement) {
        modalElement.addEventListener('shown.bs.modal', adjustModalPosition);
        modalElement.addEventListener('hidden.bs.modal', function () {
            document.getElementById('modal-body').innerHTML =
                '<div class="d-flex justify-content-center align-items-center h-100 min-vh-0" style="min-height: 200px;"><div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading...</p></div></div>';
            document.getElementById('detailModalLabel').textContent = 'Detail';
        });

        modalElement.addEventListener('click', function (e) {
            if (e.target === this) {
                closeModal();
            }
        });
    }

    // 监听窗口大小变化
    window.addEventListener('resize', function () {
        const modalElement = document.getElementById('detailModal');
        if (modalElement && modalElement.classList.contains('show')) {
            adjustModalPosition();
        }
    });

    // 键盘快捷键
    document.addEventListener('keydown', function (e) {
        const modal = document.getElementById('detailModal');
        if (e.key === 'Escape' && modal && modal.classList.contains('show')) {
            closeModal();
        }
    });

    // 读取URL参数
    const urlParams = new URLSearchParams(window.location.search);

    // 检查URL参数并打开对应模态框
    //development?modal=detail&detail=TSM2025-002
    const modalId = urlParams.get('modal');
    const detailId = urlParams.get('detail');
    if (modalId === 'detail' && detailId) {
        // 延迟执行，等待页面完全加载
        setTimeout(() => {
            showDetail(detailId);
        }, 1000);
    }
});