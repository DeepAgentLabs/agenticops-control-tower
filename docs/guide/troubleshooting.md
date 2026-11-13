# Troubleshooting

Check the failing boundary before changing application behavior.

- Missing server command dependencies: install the API extra.
- Unauthorized: use the correct reader/writer token and pass it in the client terminal as documented.
- Empty console: register agents; the offline example does not seed the database.
- Stale posture: inspect evidence timestamps and links before inferring current health.

## Verify your environment

Run commands from the environment where you installed the package. Confirm the input file exists and matches the expected artifact contract. Keep the original evidence when diagnosing a failure.
