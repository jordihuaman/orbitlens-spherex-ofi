import { expect, test, type Page } from "@playwright/test";

const result = "5e1c78336933afa7";
const presets = [
  ["barnard", "269.452080"], ["epsindi_b", "331.043750"],
  ["wise0855", "133.795120"], ["rw_aur", "76.956330"], ["r_dra", "248.167500"],
];

// Solo el flujo búsqueda/estado se simula; navegador, HTML, JS, manifiesto,
// PNG y FITS vienen del servidor real con datos sintéticos aislados.
async function controlledSearch(page: Page, status: string, resultId: string | null = null) {
  await page.route("**/api/search", (route) => route.fulfill({
    status: 202, json: { job_id: "controlled", status: "queued",
      status_url: "/api/status/controlled", deduplicated: false },
  }));
  let polls = 0;
  await page.route("**/api/status/controlled", (route) => {
    polls += 1;
    return route.fulfill({ json: {
      job_id: "controlled", status: polls === 1 ? "running" : status,
      phase: polls === 1 ? "searching" : null,
      result_id: polls === 1 ? null : resultId,
      error: status === "error" ? "IRSA no respondió (caso controlado)" : null,
      warnings: ["Proveedor de QA controlado; no consulta IRSA"],
      counts: { processed: resultId ? 8 : 0 }, request: {},
      created_at: "2026-11-14T00:00:00Z", updated_at: "2026-11-14T00:00:00Z",
      status_url: "/api/status/controlled",
    } });
  });
}

test.afterEach(async ({ page }, info) => {
  await info.attach("environment", { contentType: "application/json", body: Buffer.from(JSON.stringify({
    browser: page.context().browser()?.version(), viewport: page.viewportSize(),
    timezone: await page.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone),
    url: page.url(), dataset: "synthetic-demo", realPhone: false,
  })) });
});

test("carga pública, cinco presets y teclado", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "OrbitLens", exact: true })).toBeVisible();
  const select = page.getByLabel("Objetivo de prueba");
  await expect(select.locator("option")).toHaveCount(6);
  await select.focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("RA (grados)", { exact: true })).toBeFocused();
  expect(errors).toEqual([]);
});

for (const [id, ra] of presets) {
  test(`preset ${id}: coordenadas de referencia y envío controlado`, async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Objetivo de prueba").selectOption(id);
    await expect(page.getByLabel("RA (grados)", { exact: true })).toHaveValue(ra);
    await expect(page.getByText("Referencia pendiente de verificación astrométrica.", { exact: false })).toBeVisible();
    await controlledSearch(page, "empty");
    const request = page.waitForRequest((req) => req.url().endsWith("/api/search"));
    await page.getByRole("button", { name: "Buscar secuencia", exact: true }).click();
    expect((await request).postDataJSON().target_name).toBe(id);
    await expect(page.getByRole("heading", { name: "Sin datos utilizables" })).toBeVisible();
  });
}

test("recarga exacta, imágenes, controles, compartir y descargas", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(`/?result=${result}`);
  await expect(page.getByRole("note")).toContainText("Demostración sintética");
  await expect(page.locator(".stage figcaption strong")).toHaveText("21 nov 2025, 0:00 UTC");
  const image = page.getByRole("img", { name: "Imagen sintética DEMO-01" });
  await expect(image).toBeVisible();
  await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Frame siguiente" }).click();
  await expect(page.getByRole("img")).toHaveAttribute("alt", "Imagen sintética DEMO-02");
  await page.getByRole("button", { name: "Frame anterior" }).click();
  await page.getByRole("slider", { name: "Seleccionar frame" }).fill("4");
  await expect(page.getByRole("img")).toHaveAttribute("alt", "Imagen sintética DEMO-05");
  await page.getByLabel("Velocidad").selectOption("300");
  await page.getByRole("button", { name: "Reproducir", exact: true }).click();
  await expect(page.getByRole("img")).not.toHaveAttribute("alt", "Imagen sintética DEMO-05");
  await page.getByRole("button", { name: "Pausa", exact: true }).click();
  await page.getByRole("button", { name: "Compartir", exact: true }).click();
  await expect(page.getByRole("button", { name: "Enlace copiado" })).toBeVisible();
  const link = await page.evaluate(() => navigator.clipboard.readText());
  expect(new URL(link).searchParams.get("result")).toBe(result);
  const other = await context.newPage();
  await other.goto(link);
  await expect(other.getByRole("heading", { name: "Secuencia temporal" })).toBeVisible();
  await other.close();
  const pngDownload = page.waitForEvent("download");
  await page.getByRole("link", { name: "PNG", exact: true }).click();
  expect(await (await pngDownload).failure()).toBeNull();
  const fitsDownload = page.waitForEvent("download");
  await page.getByRole("link", { name: "FITS derivado", exact: true }).click();
  expect(await (await fitsDownload).failure()).toBeNull();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Secuencia temporal" })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`result=${result}`));
});

test("vista sin desbordamiento y captura de evidencia", async ({ page }, info) => {
  await page.goto(`/?result=${result}`);
  await expect(page.getByRole("img")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: `test-results/${info.project.name}.png`, fullPage: true });
});

test("dos frames permiten inspección pero no reproducción", async ({ page }) => {
  const response = await page.request.get(`/api/results/${result}/manifest`);
  const manifest = await response.json();
  manifest.frames = manifest.frames.slice(0, 2);
  await page.route(`**/api/results/${result}/manifest`, (route) => route.fulfill({ json: manifest }));
  await page.goto(`/?result=${result}`);
  await expect(page.getByRole("button", { name: "Reproducir", exact: true })).toBeDisabled();
  await expect(page.getByText("Solo hay dos frames:", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Frame siguiente" }).click();
  await expect(page.getByRole("img")).toHaveAttribute("alt", "Imagen sintética DEMO-02");
});

test("entrada inválida rechazada por la API real", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("RA (grados)", { exact: true }).fill("400");
  await page.getByLabel("Dec (grados)", { exact: true }).fill("20");
  const response = page.waitForResponse((res) => res.url().endsWith("/api/search"));
  await page.getByRole("button", { name: "Buscar secuencia", exact: true }).click();
  expect((await response).status()).toBe(422);
  await expect(page.getByRole("alert")).toBeVisible();
});

test("recursos NASA y WiseView usan coordenadas y unidades explícitas", async ({ page }) => {
  await page.goto("/?target=epsindi_b&fov=10");
  const link = page.getByRole("link", { name: "Abrir este campo en WiseView (W2)" });
  await expect(link).toBeVisible();
  const url = new URL((await link.getAttribute("href"))!);
  const params = new URLSearchParams(url.hash.slice(1));
  expect(params.get("ra")).toBe("331.04375");
  expect(params.get("size")).toBe("600");
  expect(params.get("band")).toBe("2");
  expect(params.get("synth_a")).toBe("0");
  await page.getByText("Archivos, herramientas y seis tutoriales SPHEREx", { exact: true }).click();
  await expect(page.getByRole("link", { name: "SPHEREx Data Explorer — NASA/IPAC IRSA" })).toHaveAttribute("href", "https://irsa.ipac.caltech.edu/applications/spherex");
  await expect(page.getByRole("link", { name: "Gaia — ESA, acceso MAST" })).toBeVisible();
  await page.getByLabel("Objetivo de prueba").selectOption("");
  await page.getByLabel("RA (grados)", { exact: true }).fill("400");
  await expect(link).toHaveCount(0);
});

test("sexagesimal, FOV, frames y detector conservados en petición", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Entrada sexagesimal", { exact: false }).check();
  await page.getByLabel("RA (horas)", { exact: true }).fill("22 04 10.5");
  await page.getByLabel("Dec (grados)", { exact: true }).fill("-56 46 57.5");
  await page.getByRole("combobox", { name: "Detector", exact: true }).selectOption("D2");
  await page.getByLabel("Frames solicitados").selectOption("6");
  await controlledSearch(page, "empty");
  const request = page.waitForRequest((req) => req.url().endsWith("/api/search"));
  await page.getByRole("button", { name: "Buscar secuencia", exact: true }).click();
  expect((await request).postDataJSON()).toEqual({ ra_deg: "22 04 10.5", dec_deg: "-56 46 57.5",
    sexagesimal: true, fov_arcmin: 10, frames: 6, detector: "D2" });
});

for (const [state, heading] of [["ready", "Secuencia lista"], ["partial", "Secuencia parcial"],
                               ["error", "Error"]]) {
  test(`polling y estado ${state} con proveedor controlado`, async ({ page }) => {
    await page.goto("/?target=barnard");
    await expect(page.getByLabel("RA (grados)", { exact: true })).not.toHaveValue("");
    await controlledSearch(page, state, state === "error" ? null : result);
    await page.getByRole("button", { name: "Buscar secuencia", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Procesando", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    if (state !== "error") {
      await expect(page.getByRole("heading", { name: "Secuencia temporal" })).toBeVisible();
    }
  });
}
