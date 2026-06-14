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
  const serviceId = Object.keys(current.config.services || {})[0];
  
  // Add a custom variable with the full DATABASE_URL
  if (!current.config.services[serviceId].variables) {
    current.config.services[serviceId].variables = {};
  }
  
  current.config.services[serviceId].variables["CUSTOM_DB_URL"] = {
    value: "postgresql://postgres:TbOyBkontWVcZJBDgtfWaieRoawjqoHL@acela.proxy.rlwy.net:31193/railway",
  };

  console.log("Staging variable change...");
  const staged = await client.stageEnvironmentChanges({
    environmentId,
    patch: current.config,
    merge: true,
  });
  console.log("Staged ID:", staged.id);

  console.log("Committing...");
  const deploymentId = await client.commitStagedPatch({
    environmentId,
    message: "Add CUSTOM_DB_URL env var",
  });
  console.log("Deployment ID:", deploymentId);
}

main().catch(console.error);
