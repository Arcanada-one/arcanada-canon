---
id: canon.package.knowledge-contract
kind: protocol
status: draft
runtime_eligible: false
semantic_owner: Arcanada-one/talomnia-knowledge
source_commit: dade260d0d02e3548081ddbdcff3da566e6393f5
---

# Knowledge Contract package seam

This package will distribute an explicitly reviewed projection of the existing KC2 definitions, versioned assertion store and `Resolve(G_s,T)` contract. The implementation source is `kc2/src/`; the contract reference is `architecture/knowledge-contract-v2/02-knowledge-contract.md` at the pinned commit above.

Proposed consumer profiles are `kc-minimal`, `kc-standard`, `kc-orchestrator`, `kc-external-action` and `kc-research`. They do not define a second assertion schema, replace KC2 four-valued verdicts, or confer tool permissions. Every instance must retain graph/revision pins, source assertion keys, closure/reduction rung, refusals, conflicts and receipt lineage.

Paper edits require a separate proposal and reviewed package revision before changing a runtime profile. Galaxy/Module support and modality aliases require explicit KC2 compatibility work. Current `project` support must be preserved; repository compatibility records must not become new project authority.
