import { connect } from "@/client.js";

const client = await connect();
const page = await client.page("governance", { viewport: { width: 1280, height: 800 } });

await page.goto("http://localhost:8503");
await page.waitForTimeout(3000);

await page.screenshot({ path: "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/tmp/governance.png" });

const text = await page.textContent("body").then(t => t?.slice(0, 800));
console.log("=== PAGE TEXT ===");
console.log(text);
console.log("=================");

await client.disconnect();
console.log("Screenshot: tmp/governance.png");
