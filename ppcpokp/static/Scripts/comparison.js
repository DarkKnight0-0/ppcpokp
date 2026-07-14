// 表格列配置
const tableColumns = [
    {
        field: 'model_name',
        title: 'Model Name',
        visible: false,
        formatter: modelNameFormatter
    },
    {
        field: 'id',
        title: 'ID',
        visible: true,
        width: 80,
        align: 'center'
    },
    {
        field: 'title',
        title: 'Title',
        visible: true,
        width: 200,
        formatter: titleFormatter
    },
    {
        field: 'authors',
        title: 'Authors',
        visible: true,
        width: 150,
        formatter: authorsFormatter
    },
    {
        field: 'journal_name',
        title: 'Journal',
        visible: true,
        width: 200,
        formatter: journalFormatter
    },
    {
        field: 'publication_year',
        title: 'Year',
        visible: true,
        width: 100,
        align: 'center'
    },
    {
        field: 'conclusion',
        title: 'Conclusion',
        visible: true,
        width: 200,
        formatter: conclusionFormatter
    },
    {
        field: 'literature_id',
        title: 'Literature ID',
        visible: false
    }
];

// 格式化函数
function modelNameFormatter(value) {
    return value || 'Unknown Model';
}

function authorsFormatter(value) {
    if (!value) return '';
    return `<div class="text-truncate" style="max-width: 150px;" title="${value}">${value}</div>`;
}

function titleFormatter(value, row) {
    if (!value) return '';
    return `<div class="text-truncate clickable-title" style="max-width: 200px; cursor: pointer; color: #007bff;" 
                title="${value}" onclick="showDetail('/browse/comparison-detail?id=',${row.literature_id})">${value}</div>`;
}

function journalFormatter(value) {
    if (!value) return '';
    return `<div class="text-truncate" style="max-width: 200px;" title="${value}">${value}</div>`;
}

function conclusionFormatter(value) {
    if (!value) return '';
    return `<div class="text-truncate" style="max-width: 200px;" title="${value}">${value}</div>`;
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

    return {
        model_name: $('#model_name').val() || '',
        minYear: $('#minYearInput').val() || '',
        maxYear: $('#maxYearInput').val() || '',
        target_outcome: target_outcomes,
        model_type: modelTypes
    };
}

// 重置筛选条件
function resetFilters() {
    $('#model_name').val('');
    $('input[name="target_outcome"]').prop('checked', false);
    $('input[name="model_type"]').prop('checked', false);

    // 重置滑块
    const currentYear = new Date().getFullYear();
    if (window.yearSlider) {
        window.yearSlider.set([2005, currentYear]);
    }

    refreshTable();
}

// 初始化 noUiSlider
function initNoUiSlider() {
    const currentYear = new Date().getFullYear();
    const minYear = 2010;

    const slider = document.getElementById('yearRangeSlider');
    const minYearInput = document.getElementById('minYearInput');
    const maxYearInput = document.getElementById('maxYearInput');

    if (!slider) return;

    // 如果已经存在实例，先销毁
    if (slider.noUiSlider) {
        slider.noUiSlider.destroy();
    }

    // 初始化滑块
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
            values: [2010, 2015, 2020, currentYear],
            density: 4,
            format: {
                to: function (value) {
                    return Math.round(value);
                }
            }
        }
    });

    // 监听滑块变化
    window.yearSlider.on('update', function (values) {
        const minYearSelected = Math.floor(parseFloat(values[0]));
        const maxYearSelected = Math.floor(parseFloat(values[1]));

        // 更新隐藏字段的值
        if (minYearInput) minYearInput.value = minYearSelected;
        if (maxYearInput) maxYearInput.value = maxYearSelected;
    });

    // 当滑块值改变完成时，触发表格刷新
    window.yearSlider.on('change', function (values) {
        refreshTable();
    });
}

// 页面加载完成后初始化
$(document).ready(function () {
    if (document.getElementById('yearRangeSlider')) {
        initNoUiSlider();
    }

    // 读取URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const modelTypes = urlParams.getAll('model_type');

    // 取消所有复选框的选中状态
    $('input[name="model_type"]').prop('checked', false);

    // 根据URL参数选中对应的复选框
    modelTypes.forEach(type => {
        $(`input[name="model_type"][value="${type}"]`).prop('checked', true);
    });

    const urlModelName = urlParams.get('model_name');
    if (urlModelName) {
        $('#model_name').val(urlModelName);
    }

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

    initBootstrapTable('/browse/comparison-data');


    // 绑定筛选表单的change事件
    $('#model_name').on('change keyup', function (e) {
        // 如果是输入框，延迟500ms触发刷新
        if ($(this).is('input')) {
            clearTimeout(window.searchTimeout);
            window.searchTimeout = setTimeout(refreshTable, 500);
        } else {
            refreshTable();
        }
    });

    // 绑定复选框的change事件
    $('input[name="target_outcome"]').on('change', refreshTable);
    $('input[name="model_type"]').on('change', refreshTable);

    // 绑定模态框事件
    const modalElement = document.getElementById('detailModal');
    if (modalElement) {
        modalElement.addEventListener('shown.bs.modal', adjustModalPosition);
        modalElement.addEventListener('hidden.bs.modal', function () {
            document.getElementById('modal-body').innerHTML =
                '<div class="d-flex justify-content-center align-items-center h-100 min-vh-0" style="min-height: 200px;"><div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div><p class="mt-2">正在加载文献详情...</p></div></div>';
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


    // 检查URL参数并打开对应模态框
    //comparison?modal=detail&detail=1
    const modalId = urlParams.get('modal');
    const detailId = urlParams.get('detail');
    if (modalId === 'detail' && detailId) {
        // 延迟执行，等待页面完全加载
        setTimeout(() => {
            showDetail('/browse/comparison-detail?id=', detailId);
        }, 1000);
    }
});