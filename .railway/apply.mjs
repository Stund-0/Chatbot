import { evaluateRailwayFile, IacClient } from "railway/iac";
import { readFileSync } from "fs";
import path from "path";
import os from "os";

async function main() {
  const projectId = "8cb4759a-b205-4768-a153-82cab1f3bfaf";
  const environmentId = "534a7cf3-72cc-4fd3-9a3d-84280d11e27e";

  // Read token from CLI config
  const configPath = path.join(os.homedir(), ".railway", "config.json");
  const config = JSON.parse(readFileSync(configPath, "utf-8"));
  const token = config.user?.accessToken;

  if (!token) {
    console.error("No token found");
    process.exit(1);
  }

  console.log("Token found, creating IacClient...");

  const client = new IacClient({
    token,
    endpoint: "https://backboard.railway.com/graphql/v2",
  });

  console.log("Getting current environment...");
  const current = await client.getCurrentEnvironment(environmentId);
  console.log("Current services:", Object.keys(current.config.services || {}));

  // Modify the start command for the web service
  if (current.config.services?.web) {
    current.config.services.web.deploy = {
      ...(current.config.services.web.deploy || {}),
      startCommand: "python run.py",
    };
    console.log("Updated startCommand to 'python run.py'");
  }

  console.log("Staging changes...");
  const staged = await client.stageEnvironmentChanges({
    environmentId,
    patch: current.config,
    merge: true,
  });
  console.log("Staged:", JSON.stringify(staged));

  console.log("Committing staged patch...");
  const deploymentId = await client.commitStagedPatch({
    environmentId,
    message: "Update start command to python run.py",
  });
  console.log("Deployment ID:", deploymentId);
  console.log("Done! Check Railway dashboard for deploy status.");
}

main().catch(console.error);
