import { defineConfig } from "orval";

// Generates a fully-typed API client + TanStack Query hooks from the FastAPI
// OpenAPI spec. Workflow:
//   1. Refresh the spec:  curl <API>/openapi.json -o web/openapi.json
//   2. Generate code:     npm run gen
// Output lands in src/api/generated/. The custom axios instance in
// src/api/mutator.ts injects the base URL + bearer token.
export default defineConfig({
  ragassist: {
    input: "./openapi.json",
    output: {
      mode: "tags-split",
      target: "./src/api/generated",
      schemas: "./src/api/generated/model",
      client: "react-query",
      prettier: false,
      override: {
        mutator: {
          path: "./src/api/mutator.ts",
          name: "customInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
