```md
# SDLC-SPDD Orchestrator Project Spec

## Purpose

Create a new GitHub repository that combines the strongest ideas from two existing frameworks:

- SDLC Agents: `https://github.com/dsilahcilar/sdlc-agents`
- OpenSPDD: `https://github.com/gszhangwei/open-spdd`

The goal is to create a Cursor-first AI software delivery scaffold that makes AI-assisted development more disciplined, repeatable, and reviewable.

This project should combine:

- SDLC Agents' multi-agent software delivery lifecycle
- OpenSPDD's structured prompt-driven development model
- A REASONS Canvas design-contract artifact
- Cursor command templates
- Project memory
- Architecture safeguards
- Review and sync workflows

The first version should not attempt to become a full runtime or deeply fork either upstream framework. It should be a practical integration/scaffold repository that can be copied into or installed into real projects.

## Preferred Repository Name

Use:

    sdlc-spdd-orchestrator

Alternative names:

    agentic-sdlc-spdd
    cursor-sdlc-orchestrator
    spdd-agentic-devflow
    sdlc-reasons-orchestrator

Preferred GitHub repo:

    jmjava/sdlc-spdd-orchestrator

## Core Thesis

SDLC Agents should own the process.

OpenSPDD should own the artifact structure.

Cursor should be the initial execution environment.

The combined system should turn messy feature requests into structured implementation contracts and then guide AI coding tools through planning, architecture review, coding, review, retro, and sync.

The workflow should be:

    User Requirement
      -> SDLC Initializer Agent
      -> SDLC Planning Agent
      -> OpenSPDD-style REASONS Canvas
      -> SDLC Architect Agent
      -> Implementation Task Breakdown
      -> SDLC Coding Agent
      -> SDLC Code Review Agent
      -> SDLC Retro Agent
      -> SPDD Sync Agent
      -> Updated project memory and design contract

## What This Project Is

This project is:

- A Cursor-first scaffold for agentic software delivery
- A structured prompt and template system
- A design-contract workflow
- A set of reusable SDLC agent roles
- A project memory and playbook system
- A way to keep AI coding work aligned with requirements
- A bridge between lifecycle-oriented SDLC Agents and artifact-oriented OpenSPDD

## What This Project Is Not

This project is not initially:

- A full autonomous agent runtime
- A replacement for Cursor
- A replacement for Claude Code, Copilot, Codex, OpenCode, or other AI coding tools
- A hard fork of SDLC Agents
- A hard fork of OpenSPDD
- A Java-only framework
- A compiled CLI as the first milestone
- A system that should make broad code changes without an explicit design contract

## Project Principles

1. Start with practical templates and scripts.
2. Do not build a complex runtime first.
3. Keep everything copyable and inspectable.
4. Use Markdown as the primary artifact format.
5. Make every feature traceable from requirement to implementation.
6. Make AI agents operate against an explicit contract.
7. Keep coding tasks small and reviewable.
8. Preserve architecture constraints and project norms.
9. Maintain project memory so future work improves.
10. Sync design artifacts when implementation reality changes.

## Framework Mapping

Map SDLC Agents concepts to OpenSPDD concepts as follows:

    SDLC Initializer Agent
      -> Creates agent context
      -> Detects stack
      -> Creates project memory
      -> Creates workspace folders
      -> Does not modify application code

    SDLC Planning Agent
      -> Converts raw requirements into REASONS Canvas
      -> Defines requirements, entities, approach, structure, operations, norms, and safeguards
      -> Does not implement code

    SDLC Architect Agent
      -> Reviews and hardens the REASONS Canvas
      -> Adds stack-specific rules
      -> Adds architecture safeguards
      -> Improves task breakdown
      -> Decides readiness for coding
      -> Does not implement code

    SDLC Coding Agent
      -> Implements exactly one approved operation at a time
      -> Follows norms and safeguards
      -> Updates progress logs
      -> Adds or updates tests
      -> Avoids unrelated refactors

    SDLC Code Review Agent
      -> Compares changed code against REASONS Canvas
      -> Checks requirements, architecture, tests, dependencies, and drift
      -> Produces review report
      -> Does not modify code unless explicitly asked

    SDLC Retro Agent
      -> Captures lessons learned
      -> Updates memory, reusable patterns, known pitfalls, and playbooks
      -> Improves future agent behavior

    SPDD Sync Agent
      -> Reconciles design contract with implementation reality
      -> Marks completed tasks
      -> Captures changed assumptions
      -> Adds follow-up work
      -> Preserves history

## REASONS Canvas Model

The REASONS Canvas is the canonical design contract for each feature, bugfix, refactor, or spike.

REASONS stands for:

    R - Requirements
    E - Entities
    A - Approach
    S - Structure
    O - Operations
    N - Norms
    S - Safeguards

Each unit of work should have exactly one primary REASONS Canvas.

The canvas should live in both:

    agent-context/features/<WORK-ID>/reasons-canvas.md
    spdd/canvas/<WORK-ID>.md

The `agent-context` copy is the feature workspace copy.

The `spdd/canvas` copy is the canonical SPDD artifact copy.

For the MVP, these can be the same content duplicated. Later versions may use symlinks, generated files, or a canonical source with projections.

## Repository Structure

Create the repo with this structure:

    sdlc-spdd-orchestrator/
    ├── README.md
    ├── LICENSE
    ├── CHANGELOG.md
    ├── CONTRIBUTING.md
    ├── docs/
    │   ├── architecture.md
    │   ├── workflow.md
    │   ├── cursor-usage.md
    │   ├── java-spring-boot-usage.md
    │   ├── tekton-usage.md
    │   ├── github-project-setup.md
    │   ├── design-decisions.md
    │   └── roadmap.md
    ├── templates/
    │   ├── reasons-canvas/
    │   │   ├── feature-template.md
    │   │   ├── bugfix-template.md
    │   │   ├── refactor-template.md
    │   │   └── spike-template.md
    │   ├── cursor/
    │   │   ├── sdlc-spdd-init.md
    │   │   ├── sdlc-spdd-plan.md
    │   │   ├── sdlc-spdd-architect.md
    │   │   ├── sdlc-spdd-code.md
    │   │   ├── sdlc-spdd-review.md
    │   │   ├── sdlc-spdd-retro.md
    │   │   └── sdlc-spdd-sync.md
    │   ├── agent-overlays/
    │   │   ├── initializer-agent.md
    │   │   ├── planning-agent.md
    │   │   ├── architect-agent.md
    │   │   ├── coding-agent.md
    │   │   ├── review-agent.md
    │   │   ├── retro-agent.md
    │   │   └── sync-agent.md
    │   ├── stack-rules/
    │   │   ├── java-spring-boot.md
    │   │   ├── gradle.md
    │   │   ├── maven.md
    │   │   ├── kubernetes.md
    │   │   ├── tekton.md
    │   │   ├── python.md
    │   │   ├── node.md
    │   │   └── docker.md
    │   └── github/
    │       ├── issue-template-feature.md
    │       ├── issue-template-bug.md
    │       ├── issue-template-refactor.md
    │       ├── issue-template-spike.md
    │       ├── pull-request-template.md
    │       └── project-board-fields.md
    ├── scripts/
    │   ├── init-project.sh
    │   ├── install-cursor-commands.sh
    │   ├── create-feature.sh
    │   ├── validate-reasons-canvas.sh
    │   ├── sync-agent-context.sh
    │   └── detect-stack.sh
    ├── examples/
    │   ├── spring-boot-order-api/
    │   │   ├── requirements/
    │   │   ├── agent-context/
    │   │   ├── spdd/
    │   │   └── README.md
    │   └── tekton-pipeline-demo/
    │       ├── requirements/
    │       ├── agent-context/
    │       ├── spdd/
    │       └── README.md
    ├── agent-context/
    │   ├── README.md
    │   ├── memory/
    │   │   ├── project-memory.md
    │   │   ├── architecture-decisions.md
    │   │   ├── known-pitfalls.md
    │   │   └── reusable-patterns.md
    │   ├── playbooks/
    │   │   ├── java-feature-playbook.md
    │   │   ├── bugfix-playbook.md
    │   │   ├── refactor-playbook.md
    │   │   └── pr-review-playbook.md
    │   ├── features/
    │   │   └── .gitkeep
    │   └── harness/
    │       ├── validation-rules.md
    │       └── quality-gates.md
    └── .github/
        ├── ISSUE_TEMPLATE/
        │   ├── feature.yml
        │   ├── bug.yml
        │   ├── refactor.yml
        │   └── spike.yml
        ├── pull_request_template.md
        └── workflows/
            └── validate-canvas.yml

## Target Project Structure After Installation

When this orchestrator is installed into a target project, it should create this structure:

    target-project/
    ├── .cursor/
    │   └── commands/
    │       ├── sdlc-spdd-init.md
    │       ├── sdlc-spdd-plan.md
    │       ├── sdlc-spdd-architect.md
    │       ├── sdlc-spdd-code.md
    │       ├── sdlc-spdd-review.md
    │       ├── sdlc-spdd-retro.md
    │       └── sdlc-spdd-sync.md
    ├── requirements/
    │   └── .gitkeep
    ├── spdd/
    │   ├── canvas/
    │   │   └── .gitkeep
    │   ├── tasks/
    │   │   └── .gitkeep
    │   ├── reviews/
    │   │   └── .gitkeep
    │   └── sync/
    │       └── .gitkeep
    └── agent-context/
        ├── memory/
        │   ├── project-memory.md
        │   ├── architecture-decisions.md
        │   ├── known-pitfalls.md
        │   └── reusable-patterns.md
        ├── playbooks/
        │   └── .gitkeep
        ├── features/
        │   └── .gitkeep
        └── harness/
            ├── validation-rules.md
            └── quality-gates.md

## Feature Folder Format

Each feature, bugfix, refactor, or spike should get a dedicated folder.

Format:

    agent-context/features/FEAT-001-short-name/
    ├── requirement.md
    ├── reasons-canvas.md
    ├── tasks/
    │   ├── T01-task-name.md
    │   ├── T02-task-name.md
    │   └── T03-task-name.md
    ├── progress-log.md
    ├── review.md
    ├── retro.md
    └── sync-log.md

## Work ID Convention

Use these prefixes:

    FEAT - Feature
    BUG - Bugfix
    REF - Refactor
    SPIKE - Investigation or proof of concept
    DOC - Documentation-only change
    TEST - Test-only change
    CHORE - Maintenance task

Examples:

    FEAT-001-order-status-api
    BUG-001-fix-null-order-total
    REF-001-extract-pricing-service
    SPIKE-001-evaluate-testcontainers
    DOC-001-add-cursor-usage-guide
    TEST-001-add-archunit-boundary-tests
    CHORE-001-cleanup-deprecated-scripts

## Cursor Commands

The project should generate the following Cursor commands:

    /sdlc-spdd-init
    /sdlc-spdd-plan
    /sdlc-spdd-architect
    /sdlc-spdd-code
    /sdlc-spdd-review
    /sdlc-spdd-retro
    /sdlc-spdd-sync

## Command: /sdlc-spdd-init

Purpose:

Initialize the current repository for SDLC-SPDD usage.

Responsibilities:

- Detect the project stack.
- Identify Java, Spring Boot, Gradle, Maven, Node, Python, Docker, Kubernetes, Tekton, and GitHub Actions files where present.
- Create `agent-context/`.
- Create `spdd/`.
- Create `requirements/`.
- Create initial project memory.
- Create initial architecture decision log.
- Create quality gates.
- Install Cursor commands if missing.
- Do not modify application source code.

Expected output files:

    .cursor/commands/sdlc-spdd-init.md
    .cursor/commands/sdlc-spdd-plan.md
    .cursor/commands/sdlc-spdd-architect.md
    .cursor/commands/sdlc-spdd-code.md
    .cursor/commands/sdlc-spdd-review.md
    .cursor/commands/sdlc-spdd-retro.md
    .cursor/commands/sdlc-spdd-sync.md
    agent-context/memory/project-memory.md
    agent-context/memory/architecture-decisions.md
    agent-context/harness/quality-gates.md
    spdd/canvas/.gitkeep
    requirements/.gitkeep

## Command: /sdlc-spdd-plan

Purpose:

Convert a raw requirement into a REASONS Canvas.

Input examples:

    /sdlc-spdd-plan @requirements/add-order-status-api.md
    /sdlc-spdd-plan Add a REST endpoint to search orders by customer email

Responsibilities:

- Read the requirement.
- Inspect relevant project files.
- Detect the stack.
- Create a feature folder under `agent-context/features/`.
- Create a REASONS Canvas under `spdd/canvas/`.
- Define Requirements.
- Define Entities.
- Define Approach.
- Define Structure.
- Define Operations.
- Define Norms.
- Define Safeguards.
- Break work into small implementation tasks.
- Do not implement code.
- Do not make broad assumptions silently.
- Record assumptions in the canvas.

Expected output:

    agent-context/features/<WORK-ID>/requirement.md
    agent-context/features/<WORK-ID>/reasons-canvas.md
    spdd/canvas/<WORK-ID>.md
    agent-context/features/<WORK-ID>/tasks/T01-<task>.md
    agent-context/features/<WORK-ID>/progress-log.md

## Command: /sdlc-spdd-architect

Purpose:

Review and strengthen the REASONS Canvas before coding.

Input example:

    /sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md

Responsibilities:

- Read the provided REASONS Canvas.
- Inspect relevant project files.
- Verify the Entities section is complete.
- Verify the Approach is realistic.
- Verify the Structure matches the project.
- Verify Operations are small and implementable.
- Add missing Norms.
- Add missing Safeguards.
- Identify architecture risks.
- Identify test strategy.
- Add Java/Spring Boot/Kubernetes/Tekton rules where relevant.
- Decide whether the feature is ready for coding.
- Do not implement code.

Readiness values:

    Ready For Coding
    Needs Clarification
    Needs Redesign
    Blocked

Expected output:

    Updated canvas
    Updated task breakdown
    Architecture notes
    Risk notes
    Required tests
    Readiness decision

## Command: /sdlc-spdd-code

Purpose:

Implement exactly one approved operation from a REASONS Canvas.

Input examples:

    /sdlc-spdd-code @spdd/tasks/FEAT-001/T01-create-domain-model.md
    /sdlc-spdd-code @spdd/canvas/FEAT-001-order-status-api.md --task T01

Responsibilities:

- Read the REASONS Canvas.
- Identify the selected task.
- Implement only the selected task.
- Follow all Norms.
- Respect all Safeguards.
- Add or update tests.
- Avoid unrelated refactors.
- Avoid broad file rewrites.
- Do not change public APIs unless the task explicitly requires it.
- Do not add dependencies unless the canvas allows it.
- Update task status.
- Update progress log.

Expected output:

    Code changes for selected task only
    Updated task status
    Updated progress log
    Test notes
    Validation notes

## Command: /sdlc-spdd-review

Purpose:

Review code changes against the REASONS Canvas.

Input example:

    /sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md

Responsibilities:

- Read the REASONS Canvas.
- Inspect changed files.
- Compare implementation to Requirements.
- Compare implementation to Entities.
- Compare implementation to Approach.
- Compare implementation to Structure.
- Verify Operations are complete.
- Verify Norms were followed.
- Verify Safeguards were respected.
- Check for missing tests.
- Check for architecture drift.
- Check for dependency changes.
- Check for API or schema changes.
- Check for unrelated refactors.
- Produce a review report.
- Do not make code changes unless explicitly asked.

Review result values:

    Approved
    Approved With Notes
    Changes Requested
    Blocked

Expected output:

    agent-context/features/<WORK-ID>/review.md
    spdd/reviews/<WORK-ID>-review.md

## Command: /sdlc-spdd-retro

Purpose:

Capture learnings after a feature, bugfix, refactor, or spike.

Input example:

    /sdlc-spdd-retro @spdd/canvas/FEAT-001-order-status-api.md

Responsibilities:

- Read the REASONS Canvas.
- Read the progress log.
- Read the review report.
- Identify what worked.
- Identify what caused friction.
- Identify reusable patterns.
- Identify project-specific pitfalls.
- Update project memory.
- Update known pitfalls.
- Update reusable patterns.

Expected output:

    agent-context/features/<WORK-ID>/retro.md
    agent-context/memory/project-memory.md
    agent-context/memory/known-pitfalls.md
    agent-context/memory/reusable-patterns.md

## Command: /sdlc-spdd-sync

Purpose:

Synchronize the design contract with implementation reality.

Input example:

    /sdlc-spdd-sync @spdd/canvas/FEAT-001-order-status-api.md

Responsibilities:

- Read the REASONS Canvas.
- Inspect implementation files.
- Identify completed operations.
- Identify changed assumptions.
- Identify implementation drift.
- Identify missing tasks.
- Identify stale tasks.
- Update the canvas while preserving useful history.
- Add follow-up tasks where needed.
- Do not implement code unless explicitly asked.

Expected output:

    agent-context/features/<WORK-ID>/reasons-canvas.md
    agent-context/features/<WORK-ID>/sync-log.md
    spdd/sync/<WORK-ID>-sync.md
    Updated spdd/canvas/<WORK-ID>.md

## REASONS Canvas Template

Create:

    templates/reasons-canvas/feature-template.md

Content:

    # REASONS Canvas: <WORK-ID> - <Work Name>

    ## Metadata

    - Work ID:
    - Work Type:
    - Status: Draft
    - Created:
    - Updated:
    - Owner:
    - Target Project:
    - Stack:
    - Related Issue:
    - Related PR:

    ## R - Requirements

    ### User Goal

    Describe what the user wants.

    ### Business / Product Goal

    Describe why this matters.

    ### Acceptance Criteria

    - [ ] Criterion 1
    - [ ] Criterion 2
    - [ ] Criterion 3

    ### Non-Goals

    - Non-goal 1
    - Non-goal 2

    ### Assumptions

    - Assumption 1
    - Assumption 2

    ### Open Questions

    - Question 1
    - Question 2

    ## E - Entities

    ### Domain Entities

    - Entity 1
    - Entity 2

    ### Application Components

    - Controller:
    - Service:
    - Repository:
    - Client:
    - Configuration:
    - Tests:

    ### External Systems

    - System 1
    - System 2

    ### Data / Persistence

    - Tables:
    - Migrations:
    - Indexes:
    - Queues:
    - Events:

    ### Files Likely Affected

    - `path/to/file`

    ## A - Approach

    ### Proposed Approach

    Describe the implementation strategy.

    ### Alternatives Considered

    1. Alternative 1
    2. Alternative 2

    ### Trade-Offs

    - Trade-off 1
    - Trade-off 2

    ### Risks

    - Risk 1
    - Risk 2

    ### Failure Modes

    - Failure mode 1
    - Failure mode 2

    ## S - Structure

    ### Files To Add

    - `path/to/new-file`

    ### Files To Modify

    - `path/to/existing-file`

    ### Package / Module Structure

    Describe expected organization.

    ### Test Structure

    Describe expected tests.

    ### Documentation Structure

    Describe expected documentation updates.

    ## O - Operations

    ### T01 - Task Name

    - Status: Not Started
    - Description:
    - Files:
    - Tests:
    - Validation:

    ### T02 - Task Name

    - Status: Not Started
    - Description:
    - Files:
    - Tests:
    - Validation:

    ### T03 - Task Name

    - Status: Not Started
    - Description:
    - Files:
    - Tests:
    - Validation:

    ## N - Norms

    ### General

    - Follow existing project conventions.
    - Prefer small, targeted changes.
    - Do not perform broad unrelated refactors.
    - Keep implementation aligned with this canvas.
    - Update this canvas if implementation reality changes.
    - Do not invent requirements that were not requested.
    - Prefer explicit assumptions over hidden assumptions.

    ### Java / Spring Boot

    - Use the Java version already configured in the project.
    - Use the Spring Boot version already configured in the project.
    - Prefer constructor injection.
    - Do not put business logic in controllers.
    - Keep services focused on use-case orchestration.
    - Keep repositories focused on persistence.
    - Use records for DTOs if the project already uses records.
    - Do not introduce Lombok unless already used.
    - Do not introduce new dependencies without justification.
    - Follow existing exception handling patterns.
    - Follow existing validation patterns.
    - Preserve existing package boundaries.

    ### Testing

    - Add or update tests for every behavior change.
    - Prefer focused unit tests for business logic.
    - Prefer integration tests for database/API behavior.
    - Use existing test frameworks and conventions.
    - Do not weaken or delete existing tests unless explicitly justified.
    - Document tests that could not be run.

    ## S - Safeguards

    - Do not change public API behavior unless required by the feature.
    - Do not change database schema without migration instructions.
    - Do not change security behavior without explicit mention.
    - Do not change authentication or authorization rules unless required.
    - Do not introduce hidden background jobs unless required.
    - Do not add network calls without documenting timeout/failure behavior.
    - Do not silently swallow exceptions.
    - Do not mark the feature complete until acceptance criteria are satisfied.
    - Do not mark the feature complete until tests pass or failures are documented.
    - Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

    ## Review Checklist

    - [ ] Requirements satisfied
    - [ ] Entities updated correctly
    - [ ] Approach followed or synced
    - [ ] Structure followed or synced
    - [ ] Operations completed
    - [ ] Norms followed
    - [ ] Safeguards respected
    - [ ] Tests added or updated
    - [ ] No unrelated refactors
    - [ ] No unexplained dependencies
    - [ ] Documentation updated if needed

    ## Sync Notes

    Use this section to track changes between original plan and final implementation.

    ## Final Status

    - Status:
    - Completed Date:
    - PR:
    - Follow-Up Tasks:

## Java / Spring Boot Stack Rules

Create:

    templates/stack-rules/java-spring-boot.md

Content:

    # Java / Spring Boot Stack Rules

    ## Defaults

    - Use the Java version configured by the project.
    - Use the Spring Boot version configured by the project.
    - Do not upgrade Java, Spring Boot, Gradle, Maven, or dependencies unless the task explicitly requires it.
    - Follow existing package structure.
    - Prefer minimal diffs.

    ## Architecture

    - Controllers handle HTTP mapping, request validation handoff, and response shaping.
    - Services own business/use-case logic.
    - Repositories own persistence.
    - Clients own external API calls.
    - Configuration classes own Spring configuration.
    - Domain models should not depend on web layer classes.
    - DTOs should not leak persistence entities unless the project already does this.
    - Package boundaries should remain consistent.

    ## Dependency Injection

    - Prefer constructor injection.
    - Avoid field injection.
    - Do not introduce global mutable state.
    - Do not introduce static service locators.

    ## Persistence

    - Follow existing JPA/JDBC/MyBatis conventions.
    - Do not modify schema without migration notes.
    - Add indexes only when justified.
    - Avoid N+1 query patterns.
    - Preserve transaction boundaries.

    ## API

    - Preserve existing response formats unless explicitly changed.
    - Preserve existing error handling conventions.
    - Add OpenAPI annotations only if the project already uses them.
    - Keep validation consistent with existing usage.

    ## Testing

    - Use JUnit 5 unless the project uses another test framework.
    - Use Mockito only where existing test style supports it.
    - Use SpringBootTest only when needed.
    - Use WebMvcTest for controller slice tests where appropriate.
    - Use DataJpaTest for repository tests where appropriate.
    - Use Testcontainers for database integration tests if already used or explicitly requested.
    - Add ArchUnit tests if architecture boundaries are important.

    ## Build

    - If Gradle wrapper exists, use `./gradlew test`.
    - If Maven wrapper exists, use `./mvnw test`.
    - If no wrapper exists, use `mvn test` or `gradle test` only when appropriate.
    - Document any tests that could not be run.

## Cursor Command Template: Init

Create:

    templates/cursor/sdlc-spdd-init.md

Content:

    # /sdlc-spdd-init

    You are the SDLC-SPDD Initializer Agent.

    Your job is to initialize this repository for SDLC-SPDD usage.

    Do not modify application source code.

    ## Required Behavior

    1. Inspect the repository structure.
    2. Detect the project stack.
    3. Create `requirements/` if missing.
    4. Create `spdd/` if missing.
    5. Create `agent-context/` if missing.
    6. Create project memory files if missing.
    7. Create quality gates if missing.
    8. Create Cursor command files if missing.
    9. Record detected stack and project structure.
    10. Do not overwrite existing context unless explicitly asked.

    ## Output

    Create or update:

    - `requirements/.gitkeep`
    - `spdd/canvas/.gitkeep`
    - `spdd/tasks/.gitkeep`
    - `spdd/reviews/.gitkeep`
    - `spdd/sync/.gitkeep`
    - `agent-context/memory/project-memory.md`
    - `agent-context/memory/architecture-decisions.md`
    - `agent-context/memory/known-pitfalls.md`
    - `agent-context/memory/reusable-patterns.md`
    - `agent-context/harness/quality-gates.md`

    Print a short summary of:

    - Detected stack
    - Created folders
    - Existing folders preserved
    - Recommended next command

## Cursor Command Template: Plan

Create:

    templates/cursor/sdlc-spdd-plan.md

Content:

    # /sdlc-spdd-plan

    You are the SDLC-SPDD Planning Agent.

    Your job is to convert the user's requirement into a REASONS Canvas design contract.

    Do not implement code.

    ## Inputs

    The user may provide:

    - A plain-language requirement
    - A path to a requirement document
    - A GitHub issue
    - A partial feature idea
    - A bug report
    - A refactor goal

    ## Required Behavior

    1. Inspect the repository structure.
    2. Detect the stack.
    3. Identify relevant files and modules.
    4. Create or update a feature folder under `agent-context/features/`.
    5. Create a REASONS Canvas under `spdd/canvas/`.
    6. Use the sections:
       - Requirements
       - Entities
       - Approach
       - Structure
       - Operations
       - Norms
       - Safeguards
    7. Break work into small implementation tasks.
    8. Do not modify source code.
    9. Do not invent requirements that were not requested.
    10. Ask for clarification only when absolutely necessary.
    11. If clarification is not essential, make reasonable assumptions and record them in the canvas.

    ## Output

    Create:

    - `agent-context/features/<WORK-ID>/requirement.md`
    - `agent-context/features/<WORK-ID>/reasons-canvas.md`
    - `spdd/canvas/<WORK-ID>.md`
    - `agent-context/features/<WORK-ID>/progress-log.md`

    Also print a short summary of:

    - Work ID
    - Main requirement
    - Files likely affected
    - Risks
    - Next recommended command

## Cursor Command Template: Architect

Create:

    templates/cursor/sdlc-spdd-architect.md

Content:

    # /sdlc-spdd-architect

    You are the SDLC-SPDD Architect Agent.

    Your job is to review and harden a REASONS Canvas before implementation.

    Do not implement code.

    ## Required Behavior

    1. Read the provided REASONS Canvas.
    2. Inspect relevant project files.
    3. Verify the Entities section is complete.
    4. Verify the Approach is realistic.
    5. Verify the Structure matches the project.
    6. Verify Operations are small and implementable.
    7. Add missing Norms.
    8. Add missing Safeguards.
    9. Identify architecture risks.
    10. Identify test strategy.
    11. Mark whether the work is ready for coding.

    ## Output

    Update the canvas with:

    - Architecture notes
    - Missing entities
    - Improved task breakdown
    - Required tests
    - Quality gates
    - Risks
    - Readiness decision

    Use one of these readiness values:

    - Ready For Coding
    - Needs Clarification
    - Needs Redesign
    - Blocked

## Cursor Command Template: Code

Create:

    templates/cursor/sdlc-spdd-code.md

Content:

    # /sdlc-spdd-code

    You are the SDLC-SPDD Coding Agent.

    Your job is to implement exactly one approved operation from a REASONS Canvas.

    ## Required Behavior

    1. Read the REASONS Canvas.
    2. Identify the selected task.
    3. Implement only that task.
    4. Follow all Norms.
    5. Respect all Safeguards.
    6. Add or update tests.
    7. Do not perform unrelated refactors.
    8. Do not change public APIs unless the selected task requires it.
    9. Do not add dependencies unless the canvas allows it.
    10. Update task status and progress log.

    ## Output

    Make code changes only for the selected task.

    Update:

    - `agent-context/features/<WORK-ID>/progress-log.md`
    - The task status inside the feature canvas or task file

    After implementation, summarize:

    - Files changed
    - Tests added
    - Validation performed
    - Risks or follow-ups

## Cursor Command Template: Review

Create:

    templates/cursor/sdlc-spdd-review.md

Content:

    # /sdlc-spdd-review

    You are the SDLC-SPDD Review Agent.

    Your job is to review code changes against the REASONS Canvas.

    Do not make code changes unless explicitly asked.

    ## Required Behavior

    1. Read the REASONS Canvas.
    2. Inspect changed files.
    3. Compare implementation to Requirements.
    4. Compare implementation to Entities.
    5. Compare implementation to Approach.
    6. Compare implementation to Structure.
    7. Verify Operations are complete.
    8. Verify Norms were followed.
    9. Verify Safeguards were respected.
    10. Check tests.
    11. Check for unrelated changes.
    12. Check for architecture drift.
    13. Check for unexplained dependencies.
    14. Produce a review report.

    ## Output

    Create or update:

    - `agent-context/features/<WORK-ID>/review.md`
    - `spdd/reviews/<WORK-ID>-review.md`

    Review result must be one of:

    - Approved
    - Approved With Notes
    - Changes Requested
    - Blocked

    Include:

    - Summary
    - Findings
    - Required changes
    - Optional improvements
    - Test gaps
    - Drift from canvas
    - Recommended next command

## Cursor Command Template: Retro

Create:

    templates/cursor/sdlc-spdd-retro.md

Content:

    # /sdlc-spdd-retro

    You are the SDLC-SPDD Retro Agent.

    Your job is to capture reusable learnings after a feature, bugfix, refactor, or spike.

    Do not implement code.

    ## Required Behavior

    1. Read the REASONS Canvas.
    2. Read the progress log.
    3. Read the review report.
    4. Identify what worked.
    5. Identify what caused friction.
    6. Identify reusable patterns.
    7. Identify project-specific pitfalls.
    8. Update project memory.

    ## Output

    Create or update:

    - `agent-context/features/<WORK-ID>/retro.md`
    - `agent-context/memory/project-memory.md`
    - `agent-context/memory/known-pitfalls.md`
    - `agent-context/memory/reusable-patterns.md`

    Include:

    - Summary
    - Lessons learned
    - Reusable patterns
    - Mistakes to avoid
    - Suggested future safeguards

## Cursor Command Template: Sync

Create:

    templates/cursor/sdlc-spdd-sync.md

Content:

    # /sdlc-spdd-sync

    You are the SDLC-SPDD Sync Agent.

    Your job is to reconcile the REASONS Canvas with implementation reality.

    Do not implement code unless explicitly asked.

    ## Required Behavior

    1. Read the REASONS Canvas.
    2. Inspect implementation files.
    3. Identify completed operations.
    4. Identify changed assumptions.
    5. Identify implementation drift.
    6. Identify missing tasks.
    7. Identify stale tasks.
    8. Update the canvas while preserving useful history.
    9. Add follow-up tasks where needed.

    ## Output

    Update:

    - `agent-context/features/<WORK-ID>/reasons-canvas.md`
    - `agent-context/features/<WORK-ID>/sync-log.md`
    - `spdd/sync/<WORK-ID>-sync.md`

    Include:

    - What changed
    - What drifted
    - What was reconciled
    - What remains incomplete
    - Follow-up tasks

## Scripts

### scripts/init-project.sh

Purpose:

Initialize a target project with SDLC-SPDD files.

Usage:

    ./scripts/init-project.sh --target /path/to/project --cursor

Behavior:

- Create `.cursor/commands/` if missing.
- Copy Cursor command templates.
- Create `requirements/`.
- Create `spdd/`.
- Create `agent-context/`.
- Run stack detection.
- Create initial memory files.
- Avoid overwriting existing files unless `--force` is passed.
- Print summary of created and skipped files.

Options:

    --target <path>       Target project path
    --cursor              Install Cursor command templates
    --force               Overwrite existing generated files
    --dry-run             Show what would happen without writing files
    --help                Print usage

### scripts/install-cursor-commands.sh

Purpose:

Install or update only Cursor commands.

Usage:

    ./scripts/install-cursor-commands.sh --target /path/to/project

Behavior:

- Copy files from `templates/cursor/` into `.cursor/commands/`.
- Preserve local changes unless `--force` is passed.
- Print installed command list.

### scripts/create-feature.sh

Purpose:

Create a new feature folder and canvas from a requirement.

Usage:

    ./scripts/create-feature.sh --type feature --name "order-status-api"

Behavior:

- Determine next numeric ID for the selected type.
- Create feature folder.
- Create canvas from template.
- Create progress log.
- Create task folder.
- Create canonical `spdd/canvas` copy.

Example output:

    agent-context/features/FEAT-001-order-status-api/
    spdd/canvas/FEAT-001-order-status-api.md

### scripts/validate-reasons-canvas.sh

Purpose:

Validate that a canvas has all required sections.

Usage:

    ./scripts/validate-reasons-canvas.sh spdd/canvas/FEAT-001-order-status-api.md

Required sections:

- Metadata
- R - Requirements
- E - Entities
- A - Approach
- S - Structure
- O - Operations
- N - Norms
- S - Safeguards
- Review Checklist
- Sync Notes
- Final Status

Behavior:

- Exit 0 if valid.
- Exit non-zero if missing required sections.
- Print missing sections.
- Support validating one file or all canvases.

### scripts/detect-stack.sh

Purpose:

Detect project technologies.

Usage:

    ./scripts/detect-stack.sh --target /path/to/project

Detection rules:

    pom.xml                  -> Maven Java project
    build.gradle            -> Gradle project
    build.gradle.kts        -> Gradle Kotlin project
    src/main/java           -> Java project
    src/main/kotlin         -> Kotlin project
    package.json            -> Node project
    requirements.txt        -> Python project
    pyproject.toml          -> Python project
    Dockerfile              -> Docker project
    docker-compose.yml      -> Docker Compose project
    k8s/                    -> Kubernetes project
    kubernetes/             -> Kubernetes project
    tekton/                 -> Tekton project
    .tekton/                -> Tekton project
    .github/workflows       -> GitHub Actions project
    charts/                 -> Helm project
    Chart.yaml              -> Helm chart

Output should be written to:

    agent-context/memory/project-memory.md

### scripts/sync-agent-context.sh

Purpose:

Synchronize canonical canvas, feature workspace, progress logs, reviews, and memory.

Usage:

    ./scripts/sync-agent-context.sh --work-id FEAT-001-order-status-api

Behavior:

- Ensure feature folder exists.
- Ensure canonical canvas exists.
- Compare feature canvas and canonical canvas.
- Report drift.
- Optionally copy canonical canvas to feature folder.
- Optionally copy feature canvas to canonical canvas.
- Do not overwrite without explicit option.

Options:

    --from-canvas
    --from-feature
    --dry-run
    --force

## GitHub Project Setup

Create GitHub issues for the initial repo build.

### Issue 1: Create Initial Repository Structure

Title:

    Create initial repository structure

Body:

    ## Goal

    Create the base structure for the SDLC-SPDD Orchestrator project.

    ## Tasks

    - [ ] Add README.md
    - [ ] Add LICENSE
    - [ ] Add CHANGELOG.md
    - [ ] Add CONTRIBUTING.md
    - [ ] Add docs folder
    - [ ] Add templates folder
    - [ ] Add scripts folder
    - [ ] Add examples folder
    - [ ] Add agent-context folder
    - [ ] Add .github folder

    ## Acceptance Criteria

    - Repository structure matches project spec.
    - README explains project purpose.
    - No generated code or framework dependencies are required yet.
    - Existing upstream projects are credited but not vendored.

Labels:

    setup
    mvp
    docs

### Issue 2: Add REASONS Canvas Templates

Title:

    Add REASONS Canvas templates

Body:

    ## Goal

    Create reusable OpenSPDD-style REASONS Canvas templates for feature, bugfix, refactor, and spike workflows.

    ## Tasks

    - [ ] Add feature template
    - [ ] Add bugfix template
    - [ ] Add refactor template
    - [ ] Add spike template
    - [ ] Add validation rules
    - [ ] Add example completed canvas

    ## Acceptance Criteria

    - Each template includes Requirements, Entities, Approach, Structure, Operations, Norms, and Safeguards.
    - Templates are generic but usable for Java/Spring Boot projects.
    - Templates avoid nested code fences so they can be copied safely into Cursor.

Labels:

    templates
    mvp
    spdd

### Issue 3: Add Cursor Command Templates

Title:

    Add Cursor command templates

Body:

    ## Goal

    Create Cursor commands that implement the SDLC-SPDD lifecycle.

    ## Tasks

    - [ ] Add init command
    - [ ] Add plan command
    - [ ] Add architect command
    - [ ] Add code command
    - [ ] Add review command
    - [ ] Add retro command
    - [ ] Add sync command

    ## Acceptance Criteria

    - Commands can be copied into `.cursor/commands/`.
    - Commands are clear enough for Cursor to follow.
    - Commands enforce no-code phases where appropriate.
    - Coding command implements one approved task at a time.

Labels:

    cursor
    mvp
    templates

### Issue 4: Add Project Initialization Script

Title:

    Add project initialization script

Body:

    ## Goal

    Create a script that installs SDLC-SPDD into a target project.

    ## Tasks

    - [ ] Create `scripts/init-project.sh`
    - [ ] Add target directory argument
    - [ ] Add `--cursor` option
    - [ ] Create required folders
    - [ ] Copy command templates
    - [ ] Avoid overwriting existing files by default
    - [ ] Add `--force` option
    - [ ] Add `--dry-run` option

    ## Acceptance Criteria

    - Script can initialize a clean target project.
    - Script can safely run on an existing project.
    - Script prints a useful summary.
    - Script does not modify application source code.

Labels:

    scripts
    mvp
    install

### Issue 5: Add Java / Spring Boot Example

Title:

    Add Java / Spring Boot example

Body:

    ## Goal

    Create an example showing how SDLC-SPDD works in a Spring Boot project.

    ## Tasks

    - [ ] Add example requirement
    - [ ] Add example REASONS Canvas
    - [ ] Add example task breakdown
    - [ ] Add example review
    - [ ] Add example retro
    - [ ] Document command flow

    ## Acceptance Criteria

    - Example demonstrates feature planning through review.
    - Example includes Java/Spring Boot norms and safeguards.
    - Example shows one-task-at-a-time implementation.
    - Example is useful as a reference for real Java projects.

Labels:

    java
    spring-boot
    example

### Issue 6: Add Canvas Validation Workflow

Title:

    Add canvas validation workflow

Body:

    ## Goal

    Add a GitHub Actions workflow that validates REASONS Canvas files.

    ## Tasks

    - [ ] Add `.github/workflows/validate-canvas.yml`
    - [ ] Run `scripts/validate-reasons-canvas.sh`
    - [ ] Validate all files under `spdd/canvas/`
    - [ ] Fail when required sections are missing

    ## Acceptance Criteria

    - Pull requests fail when canvas files are malformed.
    - Workflow is simple and readable.
    - Workflow does not require external services.

Labels:

    github-actions
    validation
    mvp

## README Content

Create `README.md` with this content:

    # SDLC-SPDD Orchestrator

    A Cursor-first AI software delivery scaffold that combines SDLC Agents' multi-agent lifecycle with OpenSPDD's REASONS Canvas design-contract model.

    ## What This Is

    This project provides a practical orchestration layer for AI-assisted software development.

    It helps AI coding tools move through a disciplined lifecycle:

    1. Initialize project context
    2. Plan from requirements
    3. Create a REASONS Canvas
    4. Review architecture
    5. Implement one task at a time
    6. Review against the contract
    7. Capture retro learnings
    8. Sync design docs with implementation reality

    ## What This Is Not

    This is not initially a full agent runtime.

    It is not a replacement for Cursor, Claude Code, Copilot, OpenSPDD, or SDLC Agents.

    It is a scaffold that makes those tools more disciplined and repeatable.

    ## Why Combine SDLC Agents and OpenSPDD?

    SDLC Agents provides the software delivery lifecycle and role separation.

    OpenSPDD provides the structured design contract.

    Together they create a practical workflow where AI agents do not just generate code; they operate against an explicit contract.

    ## Quick Start

    Clone this repo:

        git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
        cd sdlc-spdd-orchestrator

    Install into a target project:

        ./scripts/init-project.sh --target /path/to/your/project --cursor

    Then in Cursor:

        /sdlc-spdd-init
        /sdlc-spdd-plan @requirements/my-feature.md
        /sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md
        /sdlc-spdd-code @spdd/tasks/FEAT-001/T01-task.md
        /sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md
        /sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md
        /sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md

    ## Recommended Workflow

        Requirement
          -> Plan
          -> Architect
          -> Code Task 1
          -> Review
          -> Code Task 2
          -> Review
          -> Retro
          -> Sync

    ## Java / Spring Boot Usage

    This scaffold works especially well for Java/Spring Boot projects because it can encode project-specific rules around:

    - Controllers
    - Services
    - Repositories
    - DTOs
    - Validation
    - Transactions
    - Tests
    - Build tooling
    - Architecture boundaries

    ## License

    MIT

    ## Attribution

    This project is inspired by:

    - SDLC Agents: multi-agent software delivery lifecycle
    - OpenSPDD: structured prompt-driven development and REASONS Canvas style design contracts

    This project is not an official extension of either project unless that relationship is established later.

## Quality Gates

Every feature should pass these gates before being considered complete:

    # Quality Gates

    - [ ] Requirement is documented
    - [ ] REASONS Canvas exists
    - [ ] Architect review completed
    - [ ] Operations are task-sized
    - [ ] Code changes map to approved operations
    - [ ] Tests added or updated
    - [ ] Review completed
    - [ ] Safeguards checked
    - [ ] Retro completed
    - [ ] Canvas synced with implementation

## MVP Definition

The MVP is complete when:

- The repo has the documented structure.
- A user can run `init-project.sh` against a Java/Spring Boot repo.
- Cursor commands are installed.
- A requirement can be turned into a REASONS Canvas.
- An architect command can harden the canvas.
- A coding command can implement one task.
- A review command can compare implementation to the canvas.
- A retro command can update memory.
- A sync command can reconcile the canvas with code.
- Canvas validation can run locally.
- Canvas validation can run in GitHub Actions.

## First Implementation Plan

Build in this order:

    Phase 1: Repository skeleton
    Phase 2: REASONS Canvas templates
    Phase 3: Cursor command templates
    Phase 4: Init/install scripts
    Phase 5: Java/Spring Boot stack rules
    Phase 6: Example Spring Boot workflow
    Phase 7: Validation scripts
    Phase 8: GitHub issue and PR templates
    Phase 9: GitHub Actions validation workflow
    Phase 10: Optional CLI wrapper
    Phase 11: Optional deeper integration with OpenSPDD and SDLC Agents

## Cursor Implementation Instructions

When implementing this project in Cursor:

1. Start by creating the repository structure exactly as specified.
2. Do not build a complex CLI first.
3. Create templates before scripts.
4. Create scripts after templates exist.
5. Keep shell scripts simple and readable.
6. Add comments explaining where future customization should happen.
7. Do not vendor large portions of either upstream framework.
8. Preserve attribution to both inspiration projects.
9. Use MIT license unless there is a reason not to.
10. Prioritize practical usability over theoretical agent runtime design.
11. Make every file useful to an actual project workflow.
12. Keep commands safe by default.
13. Keep no-code phases no-code.
14. Keep coding phases limited to one approved task at a time.

## Future Enhancements

After MVP, consider adding:

- A lightweight CLI in Go, Node, or Python
- OpenSPDD command compatibility
- SDLC Agents memory import/export
- GitHub issue generation from canvas
- GitHub PR review generation from canvas
- Tekton pipeline for validation
- ArchUnit integration for Java projects
- Project-specific rule packs
- Cursor rule generation
- Claude Code command generation
- Codex command generation
- OpenCode command generation
- Web UI for viewing feature status
- SQLite or JSON index for feature metadata
- DAG view of requirements to tasks to files to tests
- Integration with `tekton-dag`
- Integration with `datadog-drilldown`
- Integration with CourseForge app development workflows

## Development Constraints

- Keep the repository simple.
- Prefer Markdown and shell scripts for MVP.
- Avoid unnecessary dependencies.
- Avoid complex build systems until required.
- Avoid hidden behavior.
- Preserve user control.
- Make all generated files inspectable.
- Make every command safe to run in an existing project.
- Do not overwrite user files without `--force`.
- Always support `--dry-run` for scripts that write files.
- Document assumptions.

## Done Criteria For Initial Repo Creation

The initial repo creation task is done when:

- All top-level folders exist.
- README exists.
- LICENSE exists.
- At least one REASONS Canvas template exists.
- At least all seven Cursor command templates exist.
- `scripts/init-project.sh` exists.
- `scripts/detect-stack.sh` exists.
- `scripts/validate-reasons-canvas.sh` exists.
- `templates/stack-rules/java-spring-boot.md` exists.
- Example Spring Boot folder exists.
- GitHub issue templates exist.
- GitHub PR template exists.
- There is enough documentation for Cursor to continue implementation without needing another high-level explanation.
```
