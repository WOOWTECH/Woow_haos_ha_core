# Official Core baseline

## Decision

Create a separate WOOWTECH/Woow_haos_ha_core repository rather than alter or rename the branded multi-core repository. Match the observed Podman baseline, official HA Core2026.9.1. Existing k3s defaults remain stable and must be overridden explicitly for tests.

## Alternatives

1. Reference the official image directly as an add-on image: smallest configuration, but does not supply the explicit add-on packaging labels or filter Supervisor-injected environment credentials before starting Core.
2. **Chosen:** derive a minimal image from the official pinned base, add only packaging labels and an entrypoint environment filter, then execute upstream /init. Core binaries/frontend/layers are not rebuilt.
3. Fork/rebuild Core or reuse the branded image/seed scripts: rejected; increases differences from Podman/k3s and is unnecessary for version alignment.

## Scope

One independent Core add-on, amd64/aarch64, isolated/config, manual boot, cold backup, no default host port or hardware/API access. Preserve upstream/init behavior after removing Supervisor discovery/credential environment variables from the main process. No configuration mutation/seed in the wrapper.

## Non-goals

Replacing/upgrading HAOS main Core, migrating SQLite toPostgreSQL, translating arbitrary backup formats, bundling custom integrations, claiming native migration acceptance based on static tests, changing existing repositories or production deployments.

## Evidence baseline

Observed existing repository commits:
- Podman: f3c8bba1c5bc8a3d85fe7ac54ae74ff4986e2fb0
- k3s: a3e9f85233bc61091793dee86dfaf2ad0ee9c8d8
- Branded multi-core: c9549954990b0a2ca887cdc4893b1f485ac68189

Official2026.9.1 OCI index/platform/config digests were fetched and SHA256-checked; both supported platform configs report HA version2026.9.1 and entrypoint/init with noCMD. Pins are in/version-lock.json.

## Acceptance

Static/config/entrypoint tests first; nativeSupervisor build/install and same-version data-chain tests are separate pending gates. Check the complete/config and Recorder mode, not only the image version. Startup must not precede the restore/preboot gate for migration targets.
