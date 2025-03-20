// ECharts加载失败时的备用简易图表实现
window.echarts = window.echarts || {
    init: function(dom) {
        console.warn('使用ECharts备用实现');
        if (!dom) return null;
        
        // 清空容器并设置样式
        dom.innerHTML = '';
        dom.style.position = 'relative';
        dom.style.overflow = 'hidden';
        
        // 创建备用图表容器
        const container = document.createElement('div');
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        container.style.justifyContent = 'center';
        container.style.padding = '20px';
        container.style.boxSizing = 'border-box';
        
        // 添加提示信息
        const infoText = document.createElement('div');
        infoText.textContent = 'ECharts加载失败，显示简化图表';
        infoText.style.color = '#F56C6C';
        infoText.style.marginBottom = '15px';
        container.appendChild(infoText);
        
        // 创建简单图表对象
        const chartObj = {
            dom: dom,
            container: container,
            setOption: function(option) {
                this.renderSimpleChart(option);
            },
            renderSimpleChart: function(option) {
                if (!option || !option.series || !option.series.length) return;
                
                // 清空之前的内容
                while (container.childNodes.length > 1) {
                    container.removeChild(container.lastChild);
                }
                
                // 创建简单图表
                const chartContent = document.createElement('div');
                chartContent.style.width = '100%';
                chartContent.style.height = '200px';
                chartContent.style.display = 'flex';
                chartContent.style.alignItems = 'flex-end';
                chartContent.style.justifyContent = 'space-between';
                chartContent.style.borderBottom = '1px solid #EBEEF5';
                
                // 获取数据
                const series = option.series[0];
                const data = series.data || [];
                const max = Math.max(...data.map(v => typeof v === 'object' ? v.value : v));
                
                // 创建柱状图
                data.forEach((item, index) => {
                    const value = typeof item === 'object' ? item.value : item;
                    const percent = max > 0 ? (value / max) * 100 : 0;
                    
                    const bar = document.createElement('div');
                    bar.style.width = `${100 / data.length * 0.8}%`;
                    bar.style.height = `${percent}%`;
                    bar.style.backgroundColor = '#409EFF';
                    bar.style.position = 'relative';
                    bar.style.marginLeft = '2px';
                    bar.style.marginRight = '2px';
                    
                    // 显示数值
                    const label = document.createElement('div');
                    label.textContent = value;
                    label.style.position = 'absolute';
                    label.style.bottom = '100%';
                    label.style.left = '0';
                    label.style.right = '0';
                    label.style.textAlign = 'center';
                    label.style.fontSize = '12px';
                    label.style.color = '#606266';
                    
                    bar.appendChild(label);
                    chartContent.appendChild(bar);
                });
                
                container.appendChild(chartContent);
                
                // 如果有标题，也显示出来
                if (option.title && option.title.text) {
                    const title = document.createElement('h3');
                    title.textContent = option.title.text;
                    title.style.textAlign = 'center';
                    title.style.margin = '10px 0';
                    container.insertBefore(title, container.firstChild);
                }
            }
        };
        
        dom.appendChild(container);
        return chartObj;
    }
};

console.log('ECharts备用方案已加载'); 