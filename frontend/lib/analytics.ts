export const getSessionId = () => {
    if (typeof window === 'undefined') return null;
    let sid = localStorage.getItem('session_id');
    if (!sid) {
        sid = crypto.randomUUID();
        localStorage.setItem('session_id', sid);
    }
    return sid;
};

export const trackEvent = async (eventName: string, params: any = {}) => {
    if (typeof window === 'undefined') return;
    try {
        const sessionId = getSessionId();
        const payload = {
            event_name: eventName,
            session_id: sessionId,
            path: window.location.pathname,
            device: /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            ...params
        };
        
        // Use beacon if available for better reliability on unload, but fetch is fine for SPA
        await fetch('/api/analytics/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error('Analytics error:', e);
    }
};
