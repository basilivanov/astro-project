import { test, expect, type APIRequestContext } from "@playwright/test";

// ############################################################################
// AI_HEADER: E2E_BILLING_MOCK
// ROLE: Verify mock payment flow (Pay -> Generate -> Read).
// ############################################################################

const oneOffRuntimeEnabled = process.env.E2E_ENABLE_ONE_OFF_RUNTIME === "1";

test.describe("Mock Billing Flow", () => {
  let testId: string;

  const waitForCreateToSettle = async (page: any) => {
    await expect
      .poll(
        async () => {
          if (
            await page
              .getByTestId("create-one-off-note")
              .isVisible()
              .catch(() => false)
          ) {
            return "one-off-paywall";
          }
          if (
            await page
              .getByTestId("create-subscription-note")
              .isVisible()
              .catch(() => false)
          ) {
            return "subscription-paywall";
          }
          if (
            await page
              .getByTestId("create-premium-generate")
              .isVisible()
              .catch(() => false)
          ) {
            return "generate-ready";
          }
          if (
            await page
              .getByTestId("create-horary-textarea")
              .isVisible()
              .catch(() => false)
          ) {
            return "horary-ready";
          }
          if (
            await page
              .getByTestId("create-checkout-status")
              .isVisible()
              .catch(() => false)
          ) {
            return "checkout-status";
          }
          if (
            await page
              .getByRole("button", { name: /Оплатить 199₽/i })
              .isVisible()
              .catch(() => false)
          ) {
            return "pay-199";
          }
          if (
            await page
              .getByRole("button", { name: /Оформить подписку 299₽\/мес/i })
              .isVisible()
              .catch(() => false)
          ) {
            return "subscription-button";
          }
          if (
            await page
              .getByText(/Не удалось загрузить профиль для оформления/i)
              .isVisible()
              .catch(() => false)
          ) {
            return "profile-error";
          }
          if (
            await page
              .getByTestId("create-loading")
              .isVisible()
              .catch(() => false)
          ) {
            return "loading";
          }
          return "unknown";
        },
        { timeout: 60000 },
      )
      .not.toBe("loading");
  };

  const waitForOneOffReadBridge = async (page: any) => {
    await page.waitForURL(/\/(billing\/complete\?checkout=|create\?|read\/)/, {
      timeout: 30000,
    });

    if (page.url().includes("/billing/complete")) {
      await page.waitForURL(/\/(create\?|read\/)/, { timeout: 120000 });
    }

    if (page.url().includes("/create?")) {
      await expect(page.getByTestId("create-checkout-status")).toBeVisible({
        timeout: 30000,
      });
      await page.waitForURL(/\/read\//, { timeout: 120000 });
    }
  };

  test.beforeEach(async ({ page }) => {
    testId = Math.floor(Math.random() * 1000000 + 1000).toString();
    await page.addInitScript(
      ({ id }) => {
        window.sessionStorage.setItem("mock_telegram_user", "1");
        Object.assign(window, {
          MOCK_INIT_DATA_OVERRIDE: id,
          MOCK_USER_OVERRIDE: {
            id: parseInt(id, 10),
            first_name: "Billing",
            last_name: "Tester",
          },
        });
      },
      { id: testId },
    );
  });

  const seedProfile = async (request: APIRequestContext, initData: string) => {
    const response = await request.put("/api/users/me", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": initData,
      },
      data: {
        full_name: "Billing Tester",
        birth_date: "1990-01-01",
        birth_place: "Moscow",
        birth_lat: 55.75,
        birth_lon: 37.61,
        current_timezone: "Europe/Moscow",
      },
    });

    expect(response.ok()).toBeTruthy();
  };

  const readProfile = async (request: APIRequestContext, initData: string) => {
    const response = await request.get("/api/users/me", {
      headers: {
        "X-Telegram-Auth": initData,
      },
    });

    expect(response.ok()).toBeTruthy();
    return response.json();
  };

  test("should pass paid flow with mock checkout", async ({
    page,
    request,
  }) => {
    // 0. Setup profile via API directly
    await seedProfile(request, testId);

    // 1. Visit creation for a paid report
    await page.goto(`/create?type=natal_master&mock=1&runtime=1`);

    // Wait for loader to disappear
    await waitForCreateToSettle(page);

    // 2. Expect subscription checkout button instead of direct generate CTA
    const payBtn = page.getByRole("button", {
      name: /Оформить подписку 299₽\/мес/i,
    });
    await expect(payBtn).toBeVisible({ timeout: 20000 });

    // 3. Click "Оплатить"
    await payBtn.click();

    // 4. In mock mode, it should immediately start generation and redirect to /read/
    await page.waitForURL(/\/read\//, { timeout: 45000 });

    // 5. Verify Content
    await expect(page.locator("h1")).toBeVisible({ timeout: 15000 });
  });

  test("should handle horary pack mock checkout", async ({ page, request }) => {
    // 0. Setup profile via API directly
    await seedProfile(request, testId);

    // 1. Visit creation for horary
    await page.goto(`/create?type=horary&mock=1&runtime=1`);

    // Wait for loader to disappear
    await waitForCreateToSettle(page);

    // 2. Expect "Купить вопросы" screen
    await expect(page.getByText(/Купить вопросы/i)).toBeVisible({
      timeout: 20000,
    });

    // 3. Click "Оплатить" for the default pack
    const payBtn = page.getByRole("button", { name: /Оплатить/i });
    await payBtn.click();

    // 4. In mock mode, it should refresh profile and show "Задать вопрос"
    await expect(page.getByText(/Задать вопрос/i)).toBeVisible({
      timeout: 20000,
    });

    // 5. Fill question
    const textarea = page.getByTestId("create-horary-textarea");
    await textarea.fill("Mock payment test question");

    // 6. Submit
    await page.getByTestId("create-horary-submit").click();

    // 7. Redirect to /read/
    await page.waitForURL(/\/read\//, { timeout: 45000 });
  });

  test("should expose natal unlock indicator after direct one-off entitlement grant", async ({
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "natal_master",
        amount: 199,
        return_path: "/create?type=natal_master&mock=1&runtime=1",
        draft_payload: { report_type: "natal_master" },
      },
    });

    expect(payResponse.ok()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const profile = await readProfile(request, testId);
          return profile?.report_unlocks?.natal_master ?? 0;
        },
        { timeout: 20000 },
      )
      .toBe(1);

    const profile = await readProfile(request, testId);
    expect(
      profile?.feature_flags?.enable_one_off_entitlements_runtime,
    ).toBeTruthy();
    expect(
      profile?.feature_flags?.enable_persistent_checkout_sessions,
    ).toBeTruthy();
  });

  test("should expose month forecast unlock indicator after direct one-off entitlement grant", async ({
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "month_forecast",
        amount: 199,
        return_path: "/create?type=month_forecast&mock=1&runtime=1",
        draft_payload: { report_type: "month_forecast" },
      },
    });

    expect(payResponse.ok()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const profile = await readProfile(request, testId);
          return profile?.report_unlocks?.month_forecast ?? 0;
        },
        { timeout: 20000 },
      )
      .toBe(1);

    const profile = await readProfile(request, testId);
    expect(
      profile?.feature_flags?.enable_one_off_entitlements_runtime,
    ).toBeTruthy();
    expect(
      profile?.feature_flags?.enable_persistent_checkout_sessions,
    ).toBeTruthy();
  });

  test("should expose year forecast unlock indicator after direct one-off entitlement grant", async ({
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "year_forecast",
        amount: 499,
        return_path: "/create?type=year_forecast&mock=1&runtime=1",
        draft_payload: { report_type: "year_forecast" },
      },
    });

    expect(payResponse.ok()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const profile = await readProfile(request, testId);
          return profile?.report_unlocks?.year_forecast ?? 0;
        },
        { timeout: 20000 },
      )
      .toBe(1);

    const profile = await readProfile(request, testId);
    expect(
      profile?.feature_flags?.enable_one_off_entitlements_runtime,
    ).toBeTruthy();
    expect(
      profile?.feature_flags?.enable_persistent_checkout_sessions,
    ).toBeTruthy();
  });

  test("should expose solar return unlock indicator after direct one-off entitlement grant", async ({
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "solar_return",
        amount: 199,
        return_path: "/create?type=solar_return&mock=1&runtime=1",
        draft_payload: { report_type: "solar_return" },
      },
    });

    expect(payResponse.ok()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const profile = await readProfile(request, testId);
          return profile?.report_unlocks?.solar_return ?? 0;
        },
        { timeout: 20000 },
      )
      .toBe(1);

    const profile = await readProfile(request, testId);
    expect(
      profile?.feature_flags?.enable_one_off_entitlements_runtime,
    ).toBeTruthy();
    expect(
      profile?.feature_flags?.enable_persistent_checkout_sessions,
    ).toBeTruthy();
  });

  test("should expose synastry unlock indicator after direct one-off entitlement grant", async ({
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "synastry",
        amount: 199,
        return_path: "/create?type=synastry&mock=1&runtime=1",
        draft_payload: {
          report_type: "synastry",
          partner_name: "Partner",
          partner_birth_date: "1992-02-02T06:30",
          partner_birth_location: "London",
        },
      },
    });

    expect(payResponse.ok()).toBeTruthy();

    await expect
      .poll(
        async () => {
          const profile = await readProfile(request, testId);
          return profile?.report_unlocks?.synastry ?? 0;
        },
        { timeout: 20000 },
      )
      .toBe(1);

    const profile = await readProfile(request, testId);
    expect(
      profile?.feature_flags?.enable_one_off_entitlements_runtime,
    ).toBeTruthy();
    expect(
      profile?.feature_flags?.enable_persistent_checkout_sessions,
    ).toBeTruthy();
  });

  test("should bridge natal one-off mock checkout through billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    await page.goto("/create?type=natal_master&mock=1&runtime=1");
    await waitForCreateToSettle(page);

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
      {
        timeout: 20000,
      },
    );

    await page.getByRole("button", { name: /Оплатить 199₽/i }).click();

    await page.waitForURL(/\/read\//, { timeout: 120000 });

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should bridge month forecast one-off mock checkout through billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    await page.goto("/create?type=month_forecast&mock=1&runtime=1");
    await waitForCreateToSettle(page);

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
      {
        timeout: 20000,
      },
    );

    await page.getByRole("button", { name: /Оплатить 199₽/i }).click();

    await page.waitForURL(/\/read\//, { timeout: 120000 });

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should bridge year forecast one-off mock checkout through billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    await page.goto("/create?type=year_forecast&mock=1&runtime=1");
    await waitForCreateToSettle(page);

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
      {
        timeout: 20000,
      },
    );

    await page.getByRole("button", { name: /Оплатить 499₽/i }).click();

    await waitForOneOffReadBridge(page);

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should bridge solar return one-off mock checkout through billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    await page.goto("/create?type=solar_return&mock=1&runtime=1");
    await waitForCreateToSettle(page);

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
      {
        timeout: 20000,
      },
    );

    await page
      .getByTestId("create-solar-current-location")
      .fill("Tbilisi, Georgia");

    const createRequestPromise = page.waitForRequest((request) => {
      return (
        request.method() === "POST" &&
        request.url().includes("/api/reports/create")
      );
    });

    await page.getByRole("button", { name: /Оплатить 199₽/i }).click();

    const createRequest = await createRequestPromise;
    expect(createRequest.postDataJSON()).toMatchObject({
      report_type: "solar_return",
      solar_current_location: "Tbilisi, Georgia",
    });

    await page.waitForURL(/\/read\//, { timeout: 120000 });

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should bridge synastry one-off mock checkout through billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    await page.goto("/create?type=synastry&mock=1&runtime=1");
    await waitForCreateToSettle(page);

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
      {
        timeout: 20000,
      },
    );

    await page.getByTestId("create-synastry-partner-name").fill("Partner");
    await page
      .getByTestId("create-synastry-partner-birth-date")
      .fill("1992-02-02T06:30");
    await page
      .getByTestId("create-synastry-partner-birth-location")
      .fill("London");

    const createRequestPromise = page.waitForRequest((request) => {
      return (
        request.method() === "POST" &&
        request.url().includes("/api/reports/create")
      );
    });

    await page.getByRole("button", { name: /Оплатить 199₽/i }).click();

    const createRequest = await createRequestPromise;
    expect(createRequest.postDataJSON()).toMatchObject({
      report_type: "synastry",
      partner_name: "Partner",
      partner_birth_date: "1992-02-02T06:30",
      partner_birth_location: "London",
    });

    await waitForOneOffReadBridge(page);

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should resume synastry mock checkout from billing complete without session draft to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "synastry",
        amount: 199,
        return_path: "/create?type=synastry&mock=1&runtime=1",
        draft_payload: {
          report_type: "synastry",
          partner_name: "Partner",
          partner_birth_date: "1992-02-02T06:30",
          partner_birth_location: "London",
        },
      },
    });

    expect(payResponse.ok()).toBeTruthy();
    const payData = await payResponse.json();

    expect(payData.checkout_token).toBeTruthy();

    const createRequestPromise = page.waitForRequest((request) => {
      return (
        request.method() === "POST" &&
        request.url().includes("/api/reports/create")
      );
    });

    await page.goto(
      `/billing/complete?checkout=${payData.checkout_token}&mock=1&runtime=1`,
    );
    if (page.url().includes("/billing/complete")) {
      await page.waitForURL(/\/(create\?|read\/)/, { timeout: 120000 });
    }

    const createRequest = await createRequestPromise;
    expect(createRequest.postDataJSON()).toMatchObject({
      report_type: "synastry",
      partner_name: "Partner",
      partner_birth_date: "1992-02-02T06:30",
      partner_birth_location: "London",
    });

    if (page.url().includes("/create?")) {
      await expect(
        page.getByTestId("create-synastry-partner-name"),
      ).toHaveValue("Partner", { timeout: 30000 });
      await expect(
        page.getByTestId("create-synastry-partner-birth-date"),
      ).toHaveValue("1992-02-02T06:30");
      await expect(
        page.getByTestId("create-synastry-partner-birth-location"),
      ).toHaveValue("London");
      await expect(page.getByTestId("create-checkout-status")).toBeVisible({
        timeout: 30000,
      });
      await page.waitForURL(/\/read\//, { timeout: 120000 });
    } else {
      await page.waitForURL(/\/read\//, { timeout: 120000 });
    }

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });

  test("should resume direct mock checkout from billing complete to read", async ({
    page,
    request,
  }) => {
    test.skip(
      !oneOffRuntimeEnabled,
      "Requires ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME + ENABLE_PERSISTENT_CHECKOUT_SESSIONS",
    );

    await seedProfile(request, testId);

    const payResponse = await request.post("/api/billing/pay", {
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Auth": testId,
      },
      data: {
        product_type: "natal_master",
        amount: 199,
        return_path: "/create?type=natal_master&mock=1&runtime=1",
        draft_payload: { report_type: "natal_master" },
      },
    });

    expect(payResponse.ok()).toBeTruthy();
    const payData = await payResponse.json();

    expect(payData.checkout_token).toBeTruthy();

    await page.goto(
      `/billing/complete?checkout=${payData.checkout_token}&mock=1&runtime=1`,
    );
    if (page.url().includes("/billing/complete")) {
      await page.waitForURL(/\/(create\?|read\/)/, { timeout: 120000 });
    }

    if (page.url().includes("/create?")) {
      await expect(page.getByTestId("create-checkout-status")).toBeVisible({
        timeout: 30000,
      });
      await page.waitForURL(/\/read\//, { timeout: 120000 });
    } else {
      await page.waitForURL(/\/read\//, { timeout: 120000 });
    }

    const reportId = page.url().match(/\/read\/([^?]+)/)?.[1];
    expect(reportId).toBeTruthy();

    const accessSource = await page.evaluate(
      async ({ id, auth }) => {
        const response = await fetch(`/api/reports/${id}`, {
          headers: {
            "X-Telegram-Auth": auth,
          },
        });
        const payload = await response.json();
        return payload?.report?.access_source;
      },
      { id: reportId, auth: testId },
    );

    expect(accessSource).toBe("report_entitlement");
  });
});
