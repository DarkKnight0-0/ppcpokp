let isFirstLoad = true;

// 工具函数：将URL参数转换为对象
function urlParamsToObject() {
    const urlParams = new URLSearchParams(window.location.search);
    const result = {};

    for (const [key, value] of urlParams.entries()) {
        if (['modal', 'detail'].includes(key)) continue;

        if (result.hasOwnProperty(key)) {
            if (Array.isArray(result[key])) {
                result[key].push(value);
            } else {
                result[key] = [result[key], value];
            }
        } else {
            result[key] = value;
        }
    }

    return result;
}

// 工具函数：将对象转换为URL参数字符串
function objectToUrlParams(obj) {
    const params = new URLSearchParams();

    Object.entries(obj).forEach(([key, value]) => {
        if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
            return;
        }

        if (Array.isArray(value)) {
            value.forEach(item => {
                if (item) params.append(key, item); // 直接使用 key，不是 key + '[]'
            });
        } else {
            params.append(key, value);
        }
    });

    return params.toString();
}

// 修改后的 queryParams 函数可以简化
function queryParams(params) {
    const formData = getFilterParams();

    if (isFirstLoad) {
        Object.assign(formData, urlParamsToObject());
        isFirstLoad = false;
    }

    return {
        limit: params.limit,
        offset: params.offset,
        search: params.search,
        sort: params.sort,
        order: params.order,
        ...formData
    };
}

// 初始化Bootstrap Table
function initBootstrapTable(url) {
    const $table = $('#table');

    // 销毁现有的表格实例（如果存在）
    if ($table.data('bootstrap.table')) {
        $table.bootstrapTable('destroy');
    }

    // 初始化表格
    $table.bootstrapTable({
        url: url,
        method: 'GET', // 确保使用GET请求
        contentType: 'application/x-www-form-urlencoded',
        // 添加这个配置，防止jQuery自动添加[]
        ajaxOptions: {
            traditional: true
        },
        columns: tableColumns,
        search: true,
        searchHighlight: true,
        queryParams: queryParams,
        responseHandler: function (res) {
            // 如果后端返回的是数组，直接返回
            if (Array.isArray(res)) {
                return res;
            }
            // 如果后端返回的是对象，根据Bootstrap Table的格式处理
            if (res && res.rows) {
                return {
                    total: res.total,
                    rows: res.rows
                };
            }
            return res;
        },
        onLoadSuccess: function (data) {
            // 数据加载成功后应用分组
            setTimeout(applyGroupHeaders, 100);

            setTimeout(applyGroupHeaders, 100);
            // 设置搜索框占位符文本
            $('.bootstrap-table .search .form-control').attr('placeholder', 'Search terms');
        },
        onPostBody: function () {
            // 每次表格渲染后重新应用分组
            setTimeout(applyGroupHeaders, 50);

            setTimeout(applyGroupHeaders, 50);
            // 确保每次重绘后也设置
            $('.bootstrap-table .search .form-control').attr('placeholder', 'Search terms');
        }
    });

    console.log('Bootstrap Table 初始化完成');
}

// 刷新表格数据
function refreshTable() {
    $('#table').bootstrapTable('refresh');
}

// 应用分组头部样式
function applyGroupHeaders() {
    // 移除已有的分组头部
    $('.group-header').remove();

    // 获取当前页的数据
    const currentData = $('#table').bootstrapTable('getData');
    const visibleRows = $('#table tbody tr').not('.no-records-found');

    if (!currentData || currentData.length === 0 || visibleRows.length === 0) return;

    let currentGroup = null;

    // 遍历所有可见行
    visibleRows.each(function (index) {
        const $row = $(this);
        const rowData = currentData[index];
        if (!rowData) return;

        const modelName = rowData.model_name || 'Unknown Model';

        // 如果是新分组
        if (currentGroup !== modelName) {
            currentGroup = modelName;

            // 计算该分组的记录数
            const groupCount = currentData.filter(row => row.model_name === modelName).length;

            // 创建分组头部行
            const groupHeader = $(`
                    <tr class="group-header" style="background-color: #e3f2fd !important;">
                        <td colspan="7" style="font-weight: bold; padding: 12px 8px; border-top: 2px solid #1976d2; border-bottom: 1px solid #90caf9;">
                            <i class="fas fa-microchip mr-2"></i>
                            <span class="model-name-title">${modelName}</span>
                            <small class="text-muted ml-2">(${groupCount} records)</small>
                        </td>
                    </tr>
                `);

            // 在当前行前插入分组头部
            $row.before(groupHeader);
        }
    });
}

// 显示详情函数
function showDetail(url, id) {
    console.log("Loading detail for ID:", id);

    document.getElementById('detailModalLabel').textContent = 'Detail - Loading...';
    document.getElementById('modal-body').innerHTML =
        '<div class="d-flex justify-content-center align-items-center h-100 min-vh-0" style="min-height: 200px;"><div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading...</p></div></div>';

    // 显示模态框
    $('#detailModal').modal('show');

    // 加载详情内容
    setTimeout(() => {
        fetch(url + id)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(html => {
                document.getElementById('modal-body').innerHTML = html;
                updateModalTitle();
            })
            .catch(error => {
                console.error('Loading failed:', error);
                document.getElementById('modal-body').innerHTML =
                    '<div class="d-flex justify-content-center align-items-center h-100 min-vh-0" style="min-height: 200px;"><div class="alert alert-danger w-75 text-center">Loading failed, please try again later.</div></div>';
            });
    }, 100);
}

// 模态框相关辅助函数
function updateModalTitle() {
    const modalBody = document.getElementById('modal-body');
    const tableElement = modalBody.querySelector('table[data-modal-title]');
    let titleText = '';

    if (tableElement && tableElement.dataset.modalTitle) {
        titleText = tableElement.dataset.modalTitle.trim();
    } else {
        const titleElement = modalBody.querySelector('h1, h2, h3, .title, .detail-title');
        if (titleElement) {
            titleText = titleElement.textContent.trim();
        }
    }

    if (titleText) {
        document.getElementById('detailModalLabel').textContent =
            titleText.length > 30 ? titleText.substring(0, 30) + '...' : titleText;
    } else {
        document.getElementById('detailModalLabel').textContent = 'Detail';
    }
}

function adjustModalPosition() {
    const tableContainer = document.getElementById('table-container');
    const modalElement = document.getElementById('detailModal');

    if (tableContainer && modalElement) {
        const modalDialog = modalElement.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.position = 'absolute';
            modalDialog.style.top = '0';
            modalDialog.style.left = '0';
            modalDialog.style.width = '100%';
            modalDialog.style.height = '100%';
            modalDialog.style.margin = '0';
            modalDialog.style.maxWidth = '100%';
            modalDialog.style.zIndex = '1050';
        }

        const modalContent = modalElement.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.height = '100%';
            modalContent.style.borderRadius = '0.3rem';
            modalContent.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
        }

        const modalBody = modalElement.querySelector('.modal-body');
        if (modalBody) {
            const modalHeader = modalElement.querySelector('.modal-header');
            const modalFooter = modalElement.querySelector('.modal-footer');
            const headerHeight = modalHeader ? modalHeader.offsetHeight : 50;
            const footerHeight = modalFooter ? modalFooter.offsetHeight : 50;
            modalBody.style.maxHeight = `calc(100% - ${headerHeight + footerHeight}px)`;
            modalBody.style.overflowY = 'auto';
        }
    }
}

function closeModal() {
    const modalElement = document.getElementById('detailModal');
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    } else {
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
}