# CodeCraft Hardware Application Platform Architecture

Status: proposed architecture. This document describes a target integration
between CodeCraft Hub, CodeCraft Web Coding, APISIX Gateway and the hardware
build and device services. It does not claim that these services are already
implemented in this repository.

The editable diagram source is [codecraft-hardware-app-platform.drawio](codecraft-hardware-app-platform.drawio).

## Purpose

CodeCraft should let a user discover a hardware application, run an existing
firmware image, open a source project for remixing, and iterate with either a
user-owned coding agent or a CodeCraft-managed agent. The product must retain
the hardware context, build provenance and device history needed to make each
firmware result reviewable and reproducible.

The product is a hardware application forge. Gitea is a source-control
substrate, not the primary user-facing product. CodeCraft Hub is the discovery,
release and distribution surface; Web Coding is the creation and remix surface;
APISIX is the public API edge and policy enforcement point.

## Current boundaries

The repository currently owns device facts, Target metadata, native BSPs,
examples, platform adapters and development workflow contracts. Cloud account,
pairing, telemetry, publishing and Hub runtime services remain external. Hub
operations use the external SenseCraft CLI and its bundled Skill when an
authorized platform operation is requested.

The proposed platform therefore integrates with Hub through an explicit API or
CLI contract. It does not move Hub runtime code, account management or device
cloud services into this repository.

## Product model

The user-facing model should use hardware applications and versions rather than
exposing Git concepts as the primary workflow.

| Entity | Responsibility | Key identity |
| --- | --- | --- |
| `HardwareProfile` | Versioned board, chip, variant, interfaces, memory and supported stacks | `hardware_profile_id`, revision |
| `Project` | User-owned application with visibility, source mode and parent/remix relationship | `project_id` |
| `SourceRevision` | Immutable source state in the project repository | repository, commit digest |
| `BuildProfile` | Toolchain image, target, configuration, build and test commands | profile digest |
| `BuildRun` | One build attempt and its logs, receipt and outputs | `build_run_id` |
| `FirmwareRelease` | Immutable flashable package with compatibility, hashes and signature status | `release_id` |
| `ChangeRequest` | Agent or user proposed modification based on a fixed source revision | `change_id` |
| `AgentRun` | One bounded agent execution, including tools, sandbox and outputs | `agent_run_id` |
| `Device` | A claimed physical board or remote device bridge | `device_id` |
| `FlashSession` | A requested and completed device write with evidence | `flash_session_id` |
| `AgentConnection` | A user-approved external agent or managed model connection | `agent_connection_id` |

Two source modes are first-class:

* A **firmware-only project** contains a validated release manifest and image.
  It supports compatibility checks, download and flashing, but it has no source
  to remix.
* A **source project** contains a repository, hardware profile and build
  profile. It can produce firmware releases and supports Agent changes.

A Remix is a product-level object. For a project owned by the same user it is
implemented with a new branch and change request. A fork is reserved for an
independent project or a cross-owner contribution; users do not need to learn
that distinction during the normal flow.

## Target architecture

The diagram has three views:

1. **System Context** shows the product surfaces and infrastructure boundary.
2. **Agent Remix and Build** shows a source change from request to candidate
   firmware.
3. **Trust Boundaries and Data** shows which services may handle source,
   artifacts, untrusted code and device side effects.

### Product surfaces

#### CodeCraft Hub

Hub is the public discovery and delivery surface. It owns application pages,
hardware compatibility display, release visibility, download/flash entry
points, remix entry points and publishing metadata. A Hub item links to a
source project when source is available and to a specific immutable release for
flashing.

Hub should expose actions such as:

* `Run on my device` for a compatible release;
* `Open in Web Coding` to create a Remix from a source revision;
* `View source and build provenance`;
* `Publish my Remix` after a successful build.

#### CodeCraft Web Coding

Web Coding owns the conversational workspace, source editor, hardware context,
Agent run view, build status, diff review and candidate release flow. It should
present a user with a project version and a change request; Git branch, commit
and PR details remain available as an advanced view.

The workspace context sent to an Agent includes the selected hardware profile,
source revision, build profile, relevant device documentation, prior build
logs and the allowed tool scopes. Code is not the only context: board facts and
native build rules are required for an ESP32 change to be useful.

#### APISIX Gateway

APISIX is the single public API edge for Hub, Web Coding and external Agent
connections. It provides route selection, authentication integration, rate and
concurrency limits, request IDs, WebSocket proxying and gateway telemetry.

APISIX does not own project authorization, hardware compatibility or workflow
state. Each upstream service must authorize the requested resource and validate
the business transition again. Large uploads should use an API-issued
short-lived object-storage URL rather than passing the binary through the
gateway.

Suggested route groups are:

```text
/v1/projects/*       project and Remix service
/v1/repositories/*   source and change service
/v1/builds/*         build orchestrator
/v1/agents/*         Agent Gateway and Agent connections
/v1/releases/*       release and artifact service
/v1/devices/*        device bridge and flash service
/v1/hub/*            Hub integration and publishing
/ws/runs/*           build and Agent event stream
```

## Service planes

### Control plane

The control plane stores users, tenants, projects, hardware profiles, build
profiles, Agent runs, releases, devices and audit records in PostgreSQL. It
owns the state machine for a project and calls Gitea through its API. It must
not write directly to Gitea tables.

The control plane also owns the approval transitions:

```text
created → queued → running → candidate → approved → released
                         ↘ failed / cancelled
```

An Agent may create a candidate and request a flash. It does not receive the
authority to publish, erase or write a device by default.

### Source plane

Gitea stores source repositories, revisions, branches, pull requests and
repository permissions. The application maps its stable `project_id` to a
Gitea repository and keeps that mapping in the control plane.

The default source change flow is:

```text
base revision → temporary Agent workspace → branch → change request/PR
```

The workspace is ephemeral; the branch and change request are the durable
review record. A merged change becomes the next project baseline.

### Execution plane

The execution plane has separate worker classes:

* **Build Worker** uses a pinned ESP-IDF, Arduino or PlatformIO image and
  produces a build receipt, firmware images and logs.
* **Agent Sandbox** runs the user-selected Agent with bounded CPU, memory,
  disk, time and network capabilities. It receives a short-lived source token
  and an ephemeral workspace.
* **Device Worker** executes an approved flash or hardware-in-the-loop task
  through a local bridge or controlled device pool.

ESP-IDF images should be selected by explicit version tag and digest. A source
project must record its target, framework, dependencies, configuration and
build commands. Arduino and PlatformIO need their own pinned images and
profiles.

### Artifact plane

R2 stores upload staging objects, LFS objects where appropriate, firmware
images, build logs, reports, SBOMs and backups. The Git repository itself stays
on Gitea's persistent repository storage. R2 object keys are scoped by tenant,
project and run; the browser receives only short-lived signed upload or
download URLs.

Every release manifest should record at least:

```text
project_id
source_revision or uploaded-source digest
hardware_profile revision
target and framework
toolchain/build-image digest
partition and flash ranges
artifact hashes
signature status
build receipt and reproducibility status
```

## Agent contract

Cloud Agents and user-owned Agents use the same capability contract. The
implementation may be a REST API, Git integration, MCP server or a combination
of these, but the product semantics remain the same:

```text
context.get(project, revision, hardware_profile)
workspace.create(base_revision)
files.read / files.patch
build.run(build_profile)
tests.run
change.create
release.candidate
device.flash.request
```

The `device.flash.request` operation creates an approval request. It does not
grant the Agent direct access to a serial port or a long-lived device secret.

For a user-owned Agent, Web Coding issues a short-lived, project-scoped
connection or provides a clone/push workflow. The Agent pushes a branch and
the platform displays the resulting change request. For a managed Agent, the
platform launches the Agent Sandbox and applies the same contract internally.

## User journeys

### Upload and direct flash

1. The user selects a hardware profile in Hub.
2. The user uploads a firmware package or selects an existing release.
3. The release service validates target, chip, partition layout, image hashes
   and signature status.
4. Hub shows `Run on my device` only when compatibility is known.
5. The Device Bridge claims the board, displays the write scope and waits for
   user confirmation.
6. The Flash Session records the release digest, device identity, result and
   logs.

### Source remix with the CodeCraft Agent

1. The user chooses `Open in Web Coding` from a source-backed Hub item.
2. Web Coding creates a Remix from a selected source revision.
3. The user asks for a change, or selects a guided action such as `Fix build`
   or `Add sensor behavior`.
4. The Agent runs in a Sandbox, modifies a branch and runs the selected build.
5. Web Coding displays changed files, build logs, firmware size and a release
   candidate.
6. The user accepts, requests another iteration or discards the change.
7. An accepted change becomes the next project version and can be published to
   Hub.

### Source remix with a user-owned Agent

The user chooses `Use my Agent`, authorizes a short-lived connection, and
selects the project and scope. The external Agent receives the same hardware
context and build contract, pushes a branch or submits a change request, and
does not receive platform-admin credentials.

## Device and release safety

The platform should distinguish four trust levels:

| Level | Capability |
| --- | --- |
| 0 | View/download a release |
| 1 | Build and test source in an isolated worker |
| 2 | Create a release candidate and request a device action |
| 3 | Flash a claimed device after user approval |
| 4 | Publish a signed public release or OTA campaign |

Secure-boot or flash-encryption keys remain in a trusted signing service. They
are not mounted in Agent or build sandboxes. A direct uploaded binary without a
complete hardware and image manifest should be downloadable only; automatic
flashing requires explicit compatibility evidence.

## Delivery phases

### Phase 1: firmware delivery

Implement Hub release metadata, firmware manifest validation, R2 artifact
storage, device claim/bridge and direct flashing. Do not require source code.

### Phase 2: reproducible source builds

Add Gitea-backed source projects, versioned ESP32 build profiles, isolated build
workers, build receipts and candidate releases. Use the repository's existing
Target and firmware image concepts as the hardware/build source of truth.

### Phase 3: remix and Agent workflows

Add Remix, change requests, cloud Agent sandboxes, user-owned Agent
connections, diff review and approval. Keep all modifications reviewable and
reproducible.

### Phase 4: hardware-in-the-loop and publishing

Add device pools, serial/OTA bridges, automatic acceptance tests, signed
releases, rollback and Hub publishing workflows.

## Operating metrics

The primary product measure is time from selecting hardware to a successful
first run. Supporting measures are first-build success rate, reproducible-build
rate, Agent change acceptance rate, first-flash success rate, rollback success
rate, build duration and cost per Agent run.

## Open decisions

The following decisions are intentionally left open until product constraints
are confirmed:

* the first supported ESP32 targets and framework versions;
* whether device flashing starts with a local browser bridge or a desktop/CLI
  bridge;
* the external Agent connection protocol (Git, REST, MCP or all three);
* whether Hub releases are signed in the existing platform or by a new signing
  service;
* source visibility, remix licensing and public-project moderation;
* build and Agent quotas by tenant.
