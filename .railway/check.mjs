import { IacClient } from "railway/iac";
import { readFileSync } from "fs";
import path from "path";
import os from "os";

async function main() {
  const environmentId = "534a7cf3-72cc-4fd3-9a3d-84280d11e27e";
  const configPath = path.join(os.homedir(), ".railway", "config.json");
  const config = JSON.parse(readFileSync(configPath, "utf-8"));
  const token = config.user?.accessToken;

  const client = new IacClient({ token, endpoint: "https://backboard.railway.com/graphql/v2" });

  const current = await client.getCurrentEnvironment(environmentId, { decryptVariables: true });
  const services = current.config.services || {};
  for (const [key, svc] of Object.entries(services)) {
    console.log(`Service key: ${key}`);
    console.log(`  deploy.startCommand: ${svc.deploy?.startCommand}`);
    console.log(`  source.repo: ${svc.source?.repo}`);
    console.log(`  build.builder: ${svc.build?.builder}`);
  }
  
  // Also show current config
  console.log("\nFull services keys:", Object.keys(services));
}

main().catch(console.error);
