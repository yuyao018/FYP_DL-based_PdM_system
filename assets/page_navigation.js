(function () {
    window.dash_clientside = Object.assign({}, window.dash_clientside, {
        page_navigation: {
            render: function (path, search, session, templates) {
                path = path || '/'; search = search || '';
                const identity = session ? [session.user_id, session.role, session.organization_id] : null;
                const key = JSON.stringify([path, search, identity]);
                let active = window.__activePageNavigation;
                if (!active || active.key !== key) {
                    const id = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID()
                        : String(Date.now()) + '-' + Math.random();
                    active = {key: key, id: id};
                    window.__activePageNavigation = active;
                    window.dash_clientside.set_props('page-navigation-request', {
                        data: {id: id, pathname: path, search: search}
                    });
                    return templates.loading;
                }
                return window.dash_clientside.no_update;
            },
            complete: function (result, path, search, session) {
                const active = window.__activePageNavigation;
                const identity = session ? [session.user_id, session.role, session.organization_id] : null;
                const key = JSON.stringify([path || '/', search || '', identity]);
                // Rapid navigation can finish out of order. Never show an old page.
                if (active && active.key === key && result && result.id === active.id) return result.layout;
                return window.dash_clientside.no_update;
            }
        }
    });
})();
