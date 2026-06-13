import { defineRailway, github, project, service } from "railway/iac";

export default defineRailway(() => {
  const web = service("web", {
    source: github("Stund-0/Chatbot"),
    startCommand: "python run.py",
  });

  return project("chatbot", {
    resources: [web],
  });
});
