// One persistent widget across engine pages. Store its position only in this tab.
(() => {
    let drag = null;
    const key = 'pdm-simulation-position';
    function place(panel, x, y) {
        const rect = panel.getBoundingClientRect();
        x = Math.max(8, Math.min(x, window.innerWidth - rect.width - 8));
        y = Math.max(8, Math.min(y, window.innerHeight - rect.height - 8));
        panel.style.left = x + 'px';
        panel.style.top = y + 'px';
        panel.style.right = 'auto';
        return {x, y};
    }
    function save(position) {
        try { sessionStorage.setItem(key, JSON.stringify(position)); } catch (_) {}
    }
    document.addEventListener('pointerdown', event => {
        if (!event.target.closest('.simulation-drag-handle') || event.button !== 0) return;
        const panel = event.target.closest('#simulation-widget');
        const rect = panel.getBoundingClientRect();
        drag = {panel, dx:event.clientX - rect.left, dy:event.clientY - rect.top};
        event.target.setPointerCapture(event.pointerId);
        event.preventDefault();
    });
    document.addEventListener('pointermove', event => {
        if (drag) place(drag.panel, event.clientX - drag.dx, event.clientY - drag.dy);
    });
    function finish() {
        if (!drag) return;
        const rect = drag.panel.getBoundingClientRect();
        save({x:rect.left, y:rect.top});
        drag = null;
    }
    document.addEventListener('pointerup', finish);
    document.addEventListener('pointercancel', finish);
    document.addEventListener('click', event => {
        if (event.target.closest('.simulation-drag-handle')) event.preventDefault();
    });
    document.addEventListener('keydown', event => {
        if (!event.target.closest('.simulation-drag-handle')) return;
        const delta = {ArrowLeft:[-20,0], ArrowRight:[20,0], ArrowUp:[0,-20], ArrowDown:[0,20]}[event.key];
        if (!delta) return;
        event.preventDefault();
        const panel = event.target.closest('#simulation-widget');
        const rect = panel.getBoundingClientRect();
        save(place(panel, rect.left + delta[0], rect.top + delta[1]));
    });
    function clamp() {
        const panel = document.getElementById('simulation-widget');
        if (!panel || panel.hidden) return;
        const rect = panel.getBoundingClientRect();
        place(panel, rect.left, rect.top);
    }
    window.addEventListener('resize', clamp);
    const observer = new MutationObserver(() => {
        const panel = document.getElementById('simulation-widget');
        if (!panel || panel.dataset.dragReady) return;
        panel.dataset.dragReady = 'true';
        try {
            const saved = JSON.parse(sessionStorage.getItem(key));
            if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
                panel.style.left = saved.x + 'px'; panel.style.top = saved.y + 'px'; panel.style.right = 'auto';
            }
        } catch (_) {}
        new MutationObserver(clamp).observe(panel, {attributes:true, attributeFilter:['hidden']});
        panel.querySelector('details').addEventListener('toggle', clamp);
        clamp();
    });
    observer.observe(document.documentElement, {childList:true, subtree:true});
})();
