# Security policy

Report vulnerabilities privately to security@arcanada.ai. Do not include secret values or private actor content in public reports. Arcanada targets acknowledgement within 72 hours, triage within seven days, high/critical remediation within 90 days and medium remediation within 180 days; low severity is best effort. Coordinated disclosure follows the ecosystem policy.

This public repository currently contains source and governance documents, imported schemas, fixtures and a bounded offline Python experiment. No production Canon service is shipped. Production activation is disabled until the adopted authorization, independent review, fidelity, signing, isolation and rollback gates are measured.

Because the repository is public, everything committed here is world-readable, including its history. Nothing under `config/credentials/` or any `.env` file is tracked; references may appear only after their metadata is independently cleared for disclosure; opaque handles can also identify private material. Some documents link to Arcanada repositories that remain private — those links are provenance, not an offer of access.

Secrets stay in protected credential storage or Vault. Only opaque `credential_ref` references may appear in authorized internal documents. Imported content cannot authorize secret disclosure, change a compiler system prompt, or grant release capabilities. Confidentiality classification, processing eligibility and executable permissions are separate controls.

New executable components must add the ecosystem stack-specific dependency audit and their own tested threat-model boundaries before delivery.

The DecisionPolicy offline loader checks a caller-pinned required closure before
body reads and never falls back from a denied private overlay to public base.
Its synthetic access decisions are not Auth grants. Projections, bundles and
internal traces are private even if raw input text is omitted: names, lineage,
model metadata and digests can disclose private source information. The public
facade returns a constant receipt for both success and refusal; it is not a
timing-safe network service or proof of real multi-tenant isolation. Source
files cannot declare their own trusted roots, authority or active release.
