// Prueba manual explícita CON IRSA. No forma parte de test:e2e/CI.
// Ejecutar desde frontend/: node e2e/live-check.mjs
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { chromium, expect } from "@playwright/test";

const root = resolve("..");
const data = resolve(process.env.ORBITLENS_LIVE_DATA_DIR ?? "../data/live-http");
const output = resolve("../evidencias/operacion");
const python = process.env.ORBITLENS_PYTHON ?? resolve(process.platform === "win32" ? "../.venv/Scripts/python.exe" : "../.venv/bin/python");
const base = "http://127.0.0.1:8016";
let server;
let browser;
const evidence = { scope: "Formulario real → IRSA → resultado → reinicio; no hosting público ni teléfono físico", data_dir: "data/live-http (aislado por defecto)", started_at: new Date().toISOString() };

async function start() {
  server = spawn(python, ["-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8016", "--no-proxy-headers"], {
    cwd: root, env: { ...process.env, ORBITLENS_DATA_DIR: data, ORBITLENS_SEARCH_MAXREC: "200",
      ORBITLENS_MAX_CANDIDATES: "8", ORBITLENS_RETRY_ATTEMPTS: "1", ORBITLENS_CONNECT_TIMEOUT_S: "5",
      ORBITLENS_READ_TIMEOUT_S: "12", ORBITLENS_JOB_TIMEOUT_S: "120" },
  });
  await new Promise((ok, fail) => {
    server.stderr.on("data", (chunk) => { if (chunk.toString().includes("Uvicorn running")) ok(); });
    server.on("error", fail);
    server.on("exit", (code) => fail(new Error(`server exit ${code}`)));
  });
}

async function stop() {
  if (!server || server.exitCode !== null) return;
  const exited = new Promise((ok) => server.once("exit", ok));
  server.kill(); // Solo el proceso de prueba creado por este script.
  await exited;
}

try {
  mkdirSync(output, { recursive: true });
  await start();
  browser = await chromium.launch({ channel: process.env.ORBITLENS_BROWSER_CHANNEL ?? "msedge", headless: true });
  evidence.browser = browser.version();
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 }, timezoneId: "America/Lima" });
  await page.goto(base);
  await page.getByLabel("Objetivo de prueba").selectOption("rw_aur");
  await page.getByRole("slider").fill("4");
  await page.getByLabel("Frames solicitados").selectOption("3");
  await page.getByRole("combobox", { name: "Detector", exact: true }).selectOption("D1");
  const accepted = page.waitForResponse((response) => response.url().endsWith("/api/search"));
  await page.getByRole("button", { name: "Buscar secuencia", exact: true }).click();
  const acceptedResponse = await accepted;
  expect(acceptedResponse.status()).toBe(202);
  const job = await acceptedResponse.json();
  evidence.accepted = job;
  let terminal;
  await expect.poll(async () => {
    terminal = await (await page.request.get(`${base}${job.status_url}`)).json();
    return ["ready", "partial", "empty", "error"].includes(terminal.status);
  }, { timeout: 150000, intervals: [500, 1000, 2000] }).toBe(true);
  evidence.job = terminal;
  expect(["ready", "partial"]).toContain(terminal.status);
  expect(terminal.result_id).toBeTruthy();
  const id = terminal.result_id;
  await expect(page.getByRole("heading", { name: "Secuencia temporal", exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: "Reproducir", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Reproducir", exact: true }).click();
  await page.getByRole("button", { name: "Pausa", exact: true }).click();
  const manifest = await (await page.request.get(`${base}/api/results/${id}/manifest`)).json();
  evidence.artifact_http = [];
  for (const file of manifest.files) {
    const response = await page.request.get(`${base}/api/results/${id}/files/${file.id}`);
    evidence.artifact_http.push(response.status());
    expect(response.status()).toBe(200);
  }
  await page.screenshot({ path: resolve(output, "live-http.png"), fullPage: true });
  await stop();
  await start();
  const restored = await page.request.get(`${base}${job.status_url}`);
  evidence.restart_job_http = restored.status();
  evidence.restored_job = await restored.json();
  expect(restored.status()).toBe(200);
  expect(evidence.restored_job.result_id).toBe(id);
  expect(evidence.restored_job.status).toBe(terminal.status);
  await page.goto(`${base}/?result=${id}`);
  await expect(page.getByRole("button", { name: "Reproducir", exact: true })).toBeEnabled();
  evidence.restart_result = "opened";
  evidence.ok = true;
} catch (error) {
  evidence.ok = false;
  evidence.error = String(error);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await stop();
  evidence.finished_at = new Date().toISOString();
  writeFileSync(resolve(output, "live-http.json"), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence));
}
