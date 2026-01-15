const tg = window.Telegram?.WebApp;

async function auth() {
    const r = await fetch("/api/tg/auth", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({initData: tg?.initData || ""})
    });

    if (!r.ok) throw new Error("initData некорректный или miniapp открыт не в Telegram");
    return r.json();
}