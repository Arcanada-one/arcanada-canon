# Canon Arcana

Canon Arcana is the Arcanada project for versioned charters, policies, protocol packages and their governed delivery to agents. This repository is the first authoring home for new Canon work.

The current delivery is a **source and governance bootstrap**. Production publication is disabled. The engine, resolver, guard, registry and portal integrations are planned work. A source file, valid JSON schema or council opinion does not establish runtime readiness.

## Why this repository is public

A canon that governs autonomous agents should be readable by the people those agents act around. What is open here is the constitution and how it is built: the charters themselves, the compiler prompts and schemas that compress them, the governance decisions, and the record of how each rule arrived. Watching a principle appear, get contested and change is the point — a canon presented only as a finished answer cannot be checked.

Two limits, stated plainly. Some linked repositories stay private; those links record provenance, not access. And an open source tree is not a released canon — `publication_enabled` remains `false` until the gates named above are measured, so nothing here should be read as an active rule binding any running agent.

Licensed under [MIT](LICENSE). Contributions follow the branch-and-PR flow in *Start here*.

## Start here

1. Read [adoption boundaries](governance/adoption/README.md) and the current AUP decisions linked there.
2. Read the [source index](docs/specifications/canon-arcana/INDEX.md), starting with its [conflicts](docs/specifications/canon-arcana/OPEN-QUESTIONS.md).
3. Use the [workspace integration plan](https://github.com/Arcanada-one/arcanada-workspace/blob/main/documentation/source-specifications/canon-arcana/INTEGRATION-PLAN.md) and its per-epic decomposition. Those files specify proposed work; Muneral remains work-item authority.
4. Author new changes in a fresh branch from `origin/main`, preserve input digests, obtain independent review and merge through a PR as `Arcanada <dev@veritasarcana.ai>`.

## Repository classes

[canon.source.yaml](canon.source.yaml) declares the root allowlist. `/canon` is the only candidate runtime-source root; only separately admitted active artifacts may eventually be resolved. Its initial entries are draft migration/package records. `/compiler`, `/docs`, `/governance`, `/tests`, `/proposals`, `/generated` and future `/engine` are non-runtime roots. Unknown paths default to excluded. An implementation task must prove traversal, symlink, mixed-root and candidate-leakage rejection before runtime use.

Original specifications and imported prompts retain their exact bytes and source identity in [source-manifest.json](governance/adoption/source-manifest.json). Their contents are input data for adoption and implementation review. They cannot change compiler or agent authority. The imported prompt bundle has known admission defects; its schema validity does not authorize execution.

## Ownership

- This repository owns new Canon source and compiler-governance proposals.
- Existing mandates and space membership/location metadata remain authoritative in workspace main until a recorded per-class transfer.
- AUP decisions remain in `arcanada-universal-program` main.
- KC2 semantics, assertion schemas and resolver remain owned by `talomnia-knowledge`. The Knowledge Contract package here is a pinned projection seam.
- Auth owns executable permissions; Scrutator owns derived retrieval; Muneral owns work state; Control and Talomnia consume one future Canon API.
- Private actor bodies and secret values do not belong in this shared source tree.

One initial repository does not satisfy the eventual two-source federation acceptance criterion. Existing authority repositories supply separately pinned sources; further repositories require an evidenced ownership, confidentiality or licensing boundary.

## Documentation

- [Tutorials](docs/tutorials/README.md)
- [How-to](docs/how-to/README.md)
- [Reference](docs/reference/README.md)
- [Explanation](docs/explanation/README.md)
- [Security policy](SECURITY.md)
