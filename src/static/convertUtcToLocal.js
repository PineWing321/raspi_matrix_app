document.addEventListener("DOMContentLoaded", () => {
    const spans = document.querySelectorAll(".utc-time");
    spans.forEach(span => {
        let raw = span.textContent.trim();
        if (!raw) return;

        // If the string doesn't contain 'T' or 'Z', add them
        if (!raw.includes("T")) {
            raw = raw.replace(" ", "T");
        }
        if (!raw.endsWith("Z")) {
            raw += "Z";
        }

        const date = new Date(raw);
        if (isNaN(date)) return;

        const localString = date.toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });

        span.textContent = localString;
    });
});
