import { transferableAbortController } from "node:util";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./server";

const sample = transferableAbortController();
const NativeAbortController = sample.constructor as unknown as typeof AbortController;
const NativeAbortSignal = sample.signal.constructor as unknown as typeof AbortSignal;

globalThis.AbortController = NativeAbortController;
globalThis.AbortSignal = NativeAbortSignal;
if (typeof window !== "undefined") {
  window.AbortController = NativeAbortController;
  window.AbortSignal = NativeAbortSignal;
  window.fetch = globalThis.fetch;
}

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
