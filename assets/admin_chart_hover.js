/* Shared Overview-style hover cards for admin and degradation charts. */
(function () {
    const ids = ['admin-alert-trend', 'admin-maintenance-status',
        'da-top-drivers-chart', 'da-shap-waterfall'];
    function bind(id) {
        const host = document.getElementById(id);
        const graph = host && (host.matches('.js-plotly-plot')
            ? host : host.querySelector('.js-plotly-plot'));
        // Wait for Plotly initialization; attaching earlier can lose listeners
        // when newPlot installs the graph's event emitter.
        if (!graph || !graph.on || !graph._fullLayout || !graph._fullData
                || graph.dataset.adminHoverBound) return;
        graph.dataset.adminHoverBound = 'true';
        const degradation = id.startsWith('da-');
        const container = degradation ? host : host.parentElement;
        if (degradation) container.style.position = 'relative';
        const tip = document.createElement('div');
        Object.assign(tip.style, {
            display: 'none', position: 'absolute',
            background: 'rgba(10,20,45,0.95)',
            border: '1px solid rgba(74,158,255,0.35)', borderRadius: '8px',
            padding: '10px 14px', pointerEvents: 'none', zIndex: '21',
            minWidth: '160px', boxSizing: 'border-box',
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
        });
        container.appendChild(tip);
        function hide() { tip.style.display = 'none'; }
        function position(x) {
            const bounds = container.getBoundingClientRect();
            const size = graph._fullLayout && graph._fullLayout._size;
            const left = size ? size.l : 0;
            const right = size ? size.l + size.w : bounds.width;
            const width = tip.offsetWidth;
            let offset = x + 10;
            if (offset + width > right) offset = x - width - 10;
            tip.style.left = Math.max(left, Math.min(offset, bounds.width - width)) + 'px';
            tip.style.top = ((size ? size.t : 0) + 6) + 'px';
        }
        graph.on('plotly_hover', function (event) {
            const point = event.points && event.points[0];
            if (!point) return hide();
            const drivers = id === 'da-top-drivers-chart';
            const waterfall = id === 'da-shap-waterfall';
            const horizontal = id === 'admin-maintenance-status' || drivers;
            const metadata = waterfall ? point.customdata : null;
            const header = document.createElement('div');
            Object.assign(header.style, {
                fontWeight: '700', fontSize: '12px', color: 'white',
                marginBottom: '6px', paddingBottom: '5px',
                borderBottom: '1px solid rgba(74,158,255,0.25)'
            });
            header.textContent = waterfall ? metadata[0] : horizontal ? point.y
                : id === 'admin-alert-trend' ? point.customdata : point.x;
            tip.replaceChildren(header);
            event.points.forEach(function (p) {
                const row = document.createElement('div');
                Object.assign(row.style, {display: 'flex', alignItems: 'center',
                    gap: '7px', marginBottom: '3px', fontSize: '12px', color: '#a8d4ff'});
                const dot = document.createElement('span');
                const colors = waterfall ? metadata[3]
                    : (p.data.marker && p.data.marker.color) || '#4a9eff';
                Object.assign(dot.style, {width: '8px', height: '8px', borderRadius: '50%',
                    flexShrink: '0', background: Array.isArray(colors) ? colors[p.pointNumber] : colors});
                const label = document.createElement('span');
                label.textContent = (drivers || waterfall) ? 'SHAP' : horizontal ? 'Jobs' : p.data.name;
                const value = document.createElement('span');
                const score = waterfall ? metadata[1] : p.x;
                value.textContent = (drivers || waterfall)
                    ? (score >= 0 ? '+' : '') + Number(score).toFixed(4)
                    : horizontal ? p.x : p.y;
                Object.assign(value.style, {color: 'white', fontWeight: '700',
                    paddingLeft: '8px', borderLeft: '1px solid rgba(74,158,255,0.15)'});
                row.append(dot, label, value);
                tip.appendChild(row);
                if (waterfall) {
                    const running = document.createElement('div');
                    Object.assign(running.style, {color: '#a8d4ff', fontSize: '12px', marginTop: '3px'});
                    running.textContent = 'Running output: ' + Number(metadata[2]).toFixed(2);
                    tip.appendChild(running);
                }
            });
            tip.style.display = 'block';
            const bounds = container.getBoundingClientRect();
            const mouse = event.event;
            position(mouse && Number.isFinite(mouse.clientX)
                ? mouse.clientX - bounds.left : bounds.width / 2);
        });
        graph.on('plotly_unhover', hide);
        graph.on('plotly_beforeplot', hide);
        graph.addEventListener('mouseleave', hide);
    }
    let pending = false;
    function scan() {
        if (pending) return;
        pending = true;
        requestAnimationFrame(function () { pending = false; ids.forEach(bind); });
    }
    new MutationObserver(scan).observe(document.documentElement, {childList: true, subtree: true});
    scan();
}());
