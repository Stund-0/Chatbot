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
  console.log("Updating service:", serviceId);

  current.config.services[serviceId] = {
    ...current.config.services[serviceId],
    deploy: {
      ...(current.config.services[serviceId]?.deploy || {}),
      startCommand: "python run.py",
    },
  };

  console.log("New startCommand:", current.config.services[serviceId].deploy.startCommand);

  console.log("Staging changes...");
  const staged = await client.stageEnvironmentChanges({
    environmentId,
    patch: current.config,
    merge: true,
  });
  console.log("Staged ID:", staged.id);

  console.log("Committing...");
  const deploymentId = await client.commitStagedPatch({
    environmentId,
    message: "Update start command to python run.py",
  });
  console.log("Deployment ID:", deploymentId);
}

main().catch(console.error);
