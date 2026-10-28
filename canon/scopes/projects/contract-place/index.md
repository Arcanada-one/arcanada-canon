---
id: canon.charter.contract-place.description-candidate
kind: charter
status: draft
runtime_eligible: false
authority_domain: authority.arcanada
scope: scope.project.contract-place
owner_space: arcanada
---

# Knowledge Contract Arcana (Contract Place) project description and semantic scope

Knowledge Contract Arcana is an open, public project that collects a large share
of humanity's knowledge about meaning management and makes it available as
papers, specifications, a corpus and reference code. The public surfaces are
[https://contract.place](https://contract.place) and
[https://github.com/Arcanada-one/knowledge-contract](https://github.com/Arcanada-one/knowledge-contract).
The project is part of the Arcanada ecosystem.

## Intended work

The project publishes reviewed knowledge and the contracts that let agents select,
fit and cite it. Work items live only in Muneral (workspace project slug
`contract-place`, task prefix `KCP`). This charter does not publish secrets,
private digests or private topology.

## Surfaces (disclosure-safe)

| Surface | Role |
|---------|------|
| [knowledge-contract](https://github.com/Arcanada-one/knowledge-contract) | Public papers, specifications, schemas, tools and corpus |
| [contract-place-site](https://github.com/Arcanada-one/contract-place-site) | Public site source, published at contract.place |
| contract-place-api | Private service repository; see the open item below |

## Openness and attribution

This section states the project's normative intent. It is a descriptive canon
projection; the binding license texts live in the repositories linked below.

- **Open project.** The project is open to community contribution and free use,
  including commercial use and use inside derivative projects that keep their
  own license.
- **Attribution is mandatory.** Every reuse credits the author and links back to
  the source it was taken from. Upstream sources credited in a document stay
  credited in any derivative.
- **Licenses (no custom license).** Papers, specifications, articles, site text,
  corpus and documentation: Creative Commons Attribution 4.0 (CC BY 4.0). Code,
  schemas, tools and site code: Apache License 2.0. Third-party works keep their
  own licenses and are credited separately.
- **Names and logos are not licensed.** "Knowledge Contract Arcana", "Arcanada"
  and logos carry no trademark grant. "Based on Knowledge Contract Arcana" is
  acceptable; implying endorsement is not.
- **Attribution holder.** Pavel Valentov, Independent Researcher, ORCID
  [0009-0001-2567-4584](https://orcid.org/0009-0001-2567-4584). Copyright line:
  `Copyright 2026 Pavel Valentov and Knowledge Contract Arcana contributors`.
- **Contribution model.** Inbound equals outbound under the Developer
  Certificate of Origin 1.1 (`Signed-off-by:` on every commit). No CLA.
- **Review before publication.** A paper is published only after review; drafts
  stay unpublished and are outside this policy until then.

Normative files in the public repository:
[LICENSE](https://github.com/Arcanada-one/knowledge-contract/blob/main/LICENSE),
[LICENSE-CODE](https://github.com/Arcanada-one/knowledge-contract/blob/main/LICENSE-CODE),
[NOTICE](https://github.com/Arcanada-one/knowledge-contract/blob/main/NOTICE),
[ATTRIBUTION.md](https://github.com/Arcanada-one/knowledge-contract/blob/main/ATTRIBUTION.md).

### Open item: private API versus open project

The service repository `contract-place-api` is private by standing operator
order, while the project is declared open. Openness applies to the knowledge, the
specifications, the papers, the site and reference code; it does not apply to
the private service. This conflict is recorded and held. It is not resolved by
default and this charter does not change any repository visibility.

## Scope and ownership boundaries

- **Owner space:** Arcanada (`owner_space: arcanada`). Membership and location
  remain in the workspace `spaces/` registry.
- **Work items:** Muneral only.
- **Secrets:** Protected stores referenced by `credentials_ref` only; never in
  this public tree.

This draft transfers no writer, issuer, identity, promotion, publication or
runtime authority. It is not an admitted native project charter, an
AuthoringGrant or a compiled Canon release. `runtime_eligible` remains `false`.

## Public navigation

- [Canon source and ownership boundaries](../../../../README.md)
- [Arcanada universe charter candidate](../../universes/arcanada/index.md)
- [Arcanada ecosystem](https://arcanada.ai/en/ecosystem)

Only a reviewed source description is exposed here. No private source body,
identifier, credential, topology detail or private digest is published.
