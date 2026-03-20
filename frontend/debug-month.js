const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ baseURL: process.env.E2E_BASE_URL || "http://frontend:3000" });
  const page = await context.newPage();
  page.on("console", (msg) => console.log("console", msg.type(), msg.text()));
  page.on("pageerror", (err) => console.log("pageerror", err.message));
  page.on("requestfailed", (req) => console.log("requestfailed", req.method(), req.url(), req.failure()?.errorText));
  const testId = String(Math.floor(Math.random() * 1000000 + 1000));
  await page.addInitScript(({ id }) => {
    window.sessionStorage.setItem("mock_telegram_user", "1");
    Object.assign(window, {
      MOCK_INIT_DATA_OVERRIDE: id,
      MOCK_USER_OVERRIDE: { id: parseInt(id, 10), first_name: "Billing", last_name: "Tester" },
    });
  }, { id: testId });
  await page.goto("/");
  await page.evaluate(async (initData) => {
    await fetch("/api/users/me", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": initData
      },
      body: JSON.stringify({
        full_name: "Billing Tester",
        birth_date: "1990-01-01",
        birth_place: "Moscow",
        birth_lat: 55.75,
        birth_lon: 37.61,
        current_timezone: "Europe/Moscow"
      })
    });
  }, testId);
  console.log("seeded", testId);
  await page.goto("/create?type=month_forecast&mock=1&runtime=1", { waitUntil: "domcontentloaded" });
  console.log("after_goto", page.url());
  await page.waitForTimeout(5000);
  console.log("body", await page.locator("body").innerText());
  await browser.close();
})();
