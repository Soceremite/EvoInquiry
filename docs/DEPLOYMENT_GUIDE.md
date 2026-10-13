# Storage and deployment acceptance

EvoInquiry's research skills can read and work with existing project materials without initializing governance. A project using formal `.ei` registries needs verified storage for its complete project root: frozen inputs, executions, environment receipts and report history belong to that root.

## Choose the project storage

| Storage | Deployment requirement |
| --- | --- |
| Local Linux/macOS disk | Confirm that the volume survives the intended host/container lifecycle and has backups. Probe locks and replacement on that exact directory before initializing state. |
| Windows local disk | Run the native Windows acceptance workflow on the deployed platform. Registry locking is exclusive; directory fsync and the POSIX checkpoint helper are not certified on Windows. Use the trainer's native checkpoint facilities there. |
| Container overlay, `/tmp`, Kubernetes emptyDir | Suitable for disposable tests after probing. These are not a durable research default; a passing probe does not change their lifecycle. |
| Network, FUSE or distributed mount | Do not infer compatibility from the filesystem name. A failing local probe blocks state writes. Multi-host exclusion and crash recovery require separate deployment acceptance even if a single-host probe passes. |

Use a host-provisioned persistent volume for a long-lived project, such as an operator-managed local disk mounted at `/srv/research`. Keep `.ei` and its authority files in the project, on the same verified volume; `EI_STATE_ROOT` verifies the canonical location rather than redirecting state to a different disk. Do not place the state in temporary storage while presenting the project as durably governed.

The current acceptance host's QuarkFS project mount failed lock exclusion. A local overlay and an XFS emptyDir passed. The discovered host XFS bind was read-only, and no writable volume with a confirmed durable lifecycle was available. Consequently this release documents a deployment contract and verified probes, rather than claiming that this host has a production storage deployment.

## Inspect and probe

These commands use the extracted EvoInquiry root and an existing target directory:

```sh
# Read-only: no files, locks or project state are created.
python tools/filesystem_doctor.py --directory /srv/research/my-project

# Authorized acceptance: creates and removes only its own temporary probe.
python tools/filesystem_doctor.py --directory /srv/research/my-project --probe
```

The probe tests cross-process writer exclusion, release and reacquisition, file flush/replacement/readback, and POSIX directory fsync. It returns a nonzero exit code when a tested requirement fails. It does not initialize `.ei`, alter existing reports or repair a failing filesystem. PASS means those operations were observed to work on one host at that time; storage retention, backups, power-loss durability and multi-host behavior remain separate responsibilities.

Record the target mount, host, probe output, operator-confirmed retention lifecycle and backup location in the project's deployment notes. After storage acceptance, initialize the explicitly chosen profile:

```sh
python tools/project_registry.py --root /srv/research/my-project init \
  --project-id my-project --profile governed-v1
python tools/project_registry.py --root /srv/research/my-project audit
```

## Back up and restore

Quiesce all writers using the project's existing authorization and scheduler/process evidence. Archive the whole project, including `.ei`, immutable snapshots, report bodies, environment inputs and any checkpoint files still referenced or pinned. Store a checksum and the archive on a persistent destination. A failed lock backend may be a backup destination for immutable archives, but must not become a live registry write root merely because it stores those archives.

For restore, keep the original archive unchanged, extract into a new accepted persistent project directory, verify file identities and run read-only project/artifact audits. Confirm how environment interpreters, dataset locations and trainer arguments resolve on the new host before launching anything. Absolute execution paths are historical evidence, not automatically portable launch instructions. Local lock probing alone does not certify cross-filesystem migration, a live-writer backup or a relocated training environment.

## Upgrade or roll back the Codex plugin

Install from a clean extracted release directory. Codex CLI 0.162.1 copies local sources to its version cache; retained validation folders and Git history must stay outside that source. Keep each version's directory available and register only the selected source:

```sh
cd /path/to/evo-inquiry-VERSION
# Only when replacing an already configured source of this name:
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a fresh Codex session after the switch. Rollback uses the same commands from the preserved prior release directory. Changing the plugin version does not migrate or delete research project state. Verify that the registered marketplace, loaded plugin version and actual support-resource bytes agree; matching skill names alone is insufficient. The 1.0.0 → 1.1 development → 1.0.0 → 1.1 development sequence was executed with native discovery and complete source-byte checks, while unrelated Codex settings stayed unchanged.

The marketplace commands follow [official OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins); exact behavior and source-switch requirements above were verified with CLI 0.162.1.
