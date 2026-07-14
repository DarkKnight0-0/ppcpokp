// 工具函数 ==========================================
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

function escapeHtml(unsafe) {
    if (!unsafe) return unsafe;
    return unsafe.replace(/[&<>"]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        if (m === '"') return '&quot;';
        return m;
    });
}

function getColorByLevel(level) {
    switch (level.toLowerCase()) {
        case 'excellent':
            return { area: 'rgba(245, 203, 216, 0.5)', line: '#E91E63' };
        case 'good':
            return { area: 'rgba(233, 217, 243, 0.5)', line: '#9C27B0' };
        case 'fair':
            return { area: 'rgba(248, 224, 197, 0.5)', line: '#FF9800' };
        default: // poor
            return { area: 'rgba(228, 240, 203, 0.5)', line: '#8BC34A' };
    }
}

// 初始化单模型雷达图
function initRadarChart(containerId, item, level, isBest = false) {
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

    const colors = getColorByLevel(level);
    const radius = isBest ? '68%' : '51%';
    const nameGap = isBest ? 14 : 8;
    const axisNameFontSize = isBest ? 11 : 10;

    const option = {
        tooltip: { trigger: 'item' },
        radar: {
            indicator: indicators,
            shape: 'circle',
            radius: radius,
            center: ['50%', '50%'],
            splitNumber: 3,
            axisName: {
                color: '#666',
                fontSize: axisNameFontSize,
                fontWeight: 'bold',
                lineHeight: 14
            },
            nameGap: nameGap,
            splitArea: {
                areaStyle: {
                    color: ['rgba(52,152,219,0.1)', 'rgba(52,152,219,0.05)', 'rgba(52,152,219,0.02)']
                }
            },
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
                lineStyle: { width: 2, color: colors.line },
                areaStyle: { color: colors.area },
                itemStyle: { color: colors.line }
            }]
        }],
        grid: { top: 5, bottom: 5, left: 5, right: 5 }
    };
    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

// 详情模态框
function showDetailModal(modelId, detailUrl) {
    const modal = new bootstrap.Modal(document.getElementById('detailModal'));
    const iframeContainer = document.getElementById('iframe-container');

    // 显示加载状态
    iframeContainer.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100 w-100" style="min-height: 400px;">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading detail...</p>
            </div>
        </div>
    `;
    modal.show();

    const iframe = document.createElement('iframe');
    iframe.src = `${detailUrl}?id=${modelId}`;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    iframe.onerror = function () {
        iframeContainer.innerHTML = `<div class="alert alert-danger m-3">Failed to load detail.</div>`;
    };
    iframeContainer.innerHTML = '';
    iframeContainer.appendChild(iframe);
}

// 监听 iframe 高度调整消息
window.addEventListener('message', function (event) {
    if (event.data.type === 'iframe-resize') {
        const iframe = document.getElementById('detail-iframe');
        if (iframe) iframe.style.height = event.data.height + 'px';
    }
});