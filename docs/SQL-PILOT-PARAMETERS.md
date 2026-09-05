# What we need from the SQL and platform teams

**Purpose.** Everything needed to reach a SQL Server source and run a
proof-of-concept pilot on the **direct push** path. Fill in the right-hand column
and send it back.

**Nothing here is a secret, and nothing should be.** Where the source needs a
SQL login rather than Windows authentication, we ask for the **name of a Key
Vault secret**, never the password itself — the connector resolves it at
runtime and never writes it anywhere. No certificate file, keytab or token is
requested on any row below. If a question looks like it is asking for a
credential, please query it rather than answering it.

Example values use the reserved `contoso.local` domain.

---

## 0 · The path is settled — read this, do not answer it

**Direct push, and there is no longer a choice to make.** This section used to
ask which of two delivery paths to take, and compared them on deletion, change
detection and scheduling. **Three of those comparisons are now wrong**, and they
were wrong in the direction that pushed people towards the agent:

| The old sheet said | What is true now |
|---|---|
| Direct push **never deletes**; anything tighter than "by the next crawl" rules it out | Direct push **detects deletions itself** — an inventory diff after a full crawl, a sweep, and a guard that refuses a sweep after an incremental run. It is live-tested |
| Change detection: **you send everything, or build your own** | The engine hashes content and ACL **separately** and writes only what moved. Also live-tested |
| Direct push is for backfills; the **wrong tool for a standing sync** | It runs a standing sync. It has a single-instance run lock, run history, retention and reconciliation |

What the agent-hosted path genuinely still offers is health in the admin centre
and one firewall case rather than one per push host. Neither outweighed owning
the schedule, the state and the refusals, and the decision was taken to build on
direct push only.

**The deletion question has not gone away** — it moved. Deletion is bounded by
the crawl interval on either path, so the question is not *which path* but *how
often*, and that is 7.1 in the onboarding sheet rather than a row here.

## 1 · The SQL source

| # | What we need | Why | Your answer |
|---|---|---|---|
| 1.1 | **Server** and **database** name | The connection target. A named instance or non-default port should be given in full | |
| 1.2 | The **view** to read, as `schema.object` | We ask for a **view, not a table**. It puts the column selection, the joins and the soft-delete filter somewhere a DBA can read and `EXPLAIN`, and it lets the grant be on the view alone so the reader cannot see the base tables | |
| 1.3 | A **stable key column** and a **watermark column** (a `datetime2` maintained by the application) | The key identifies an item across runs; the watermark is what makes a run incremental. Without a reliable ascending timestamp, every run re-reads everything | |
| 1.4 | Whether rows are **soft-deleted** (a flag) or hard-deleted | A soft-delete flag inside the view is what lets removals be detected at all. Hard deletes are invisible to any query-based crawl | |
| 1.5 | Approximate **row count**, and growth per month | Sets the item budget and tells us whether the pilot approaches the tenant's Copilot item quota before any schema is designed | |
| 1.6 | A **URL template** for one record, e.g. `https://tickets.contoso.com/ticket/{0}` | Copilot cites the item by URL. Without a deep link the citation goes nowhere, which is usually noticed only after go-live | |
| 1.7 | Which columns are **free text**, and which are **filterable** values | Text is what gets matched semantically; values become refiners. Getting this wrong is expensive: a registered schema is append-only and cannot be corrected without deleting the connection and every item in it | |

## 2 · How the connector authenticates to SQL

| # | What we need | Why | Your answer |
|---|---|---|---|
| 2.1 | **Windows authentication or a SQL login?** | Windows integrated is strongly preferred: the service account is a gMSA whose password Active Directory owns and rotates, so no credential exists in the deployment to leak or expire | |
| 2.2 | If Windows: the **service account** to grant, and confirmation it has `SELECT` **on the view only** | Least privilege, and it is what makes 1.2's "grant on the view" real | |
| 2.3 | If a SQL login: the **Key Vault URI** and the **name of the secret** holding the password | We need the secret's *name*, never its value. Please do not send the password — the connector reads it from the vault at runtime, caches it in memory only, and re-reads on an authentication failure | |
| 2.4 | Any **required connection options** — encryption, a named instance, a non-default port | These go into the connection string. Note we will not set `TrustServerCertificate=true`; if the server's certificate is not trusted, that needs fixing rather than bypassing | |

## 3 · Who should see the data

| # | What we need | Why | Your answer |
|---|---|---|---|
| 3.1 | The **single Entra group object ID** — one AD group, the entitlement for this source | Control ACL-1: every item a connector writes is granted one group and nothing else. Not a list, and not a per-row derivation. **The condition this creates is that the group must be entitled to the least-accessible row in scope**, so anything narrower than the group is excluded rather than indexed | |
| 3.2 | Is access **uniform across all rows**, or does it vary per row? | The safety condition for 3.1. If different people should see different rows, this corpus cannot be indexed under one group — narrow the view until it can, or the rows that vary stay out. Row-Level Security and Dynamic Data Masking are the SQL Server features to check for, and **the connector does not detect either**, so this answer is the only control | |
| 3.3 | Is any of this content **licensed from a third party**? | Indexing licensed content is a redistribution and entitlement event. If the answer is yes, we need to see the agreement's redistribution, derived-data and AI-use clauses before designing anything | |

## 4 · Not needed — the agent-hosted path

This section asked for a Windows host, a loopback TLS certificate and a crawl
schedule run from the admin centre. **None of it is needed.** It is kept as a
heading rather than deleted so that anyone holding an older copy of this sheet can
see the rows were withdrawn deliberately, not lost.

If the agent path is ever revisited, the requirements are in
[`ADDING-A-PUSH-CONNECTOR.md`](ADDING-A-PUSH-CONNECTOR.md) and the code still
exists — but it is not maintained, and `SqlTicketsConnector` is the one project
that cannot be built on a developer machine without a protoc for its platform.

## 5 · The push host and its Graph identity

Skip this section if 0.1 and 0.2 pointed at agent-hosted.

| # | What we need | Why | Your answer |
|---|---|---|---|
| 5.1 | An **Entra app registration**: tenant ID, client ID | The push authenticates to Graph as an application. It needs `ExternalConnection.ReadWrite.OwnedBy` and `ExternalItem.ReadWrite.OwnedBy`, admin-consented | |
| 5.2 | A **certificate** for that app — the **thumbprint**, and which store it is installed in | Certificate authentication, not a client secret. We need the thumbprint of an installed certificate; the private key never leaves the machine store. If a client secret is unavoidable, it goes in Windows Credential Manager by target *name* | |
| 5.3 | Which **host** will run the push, and on what schedule | Direct push has no scheduler of its own. Something has to invoke it, and somebody has to notice when it stops | |
| 5.4 | Agreement on **who runs reconciliation, and how often** | The push detects deletions itself, but a divergence between source and index is still possible and nothing reports it unless somebody looks. `Compare-SourceToIndex.ps1` and `Compare-InventoryToIndex.ps1` are the two directions | |
| 5.4a | A **SQL Server instance for the crawl state database**, and a login that can create it | Four things need it: incremental reads, the single-instance run lock, run history, and both reconcilers. Express is sufficient — it holds item ids, hashes and run rows, never source content. **Without it the push reads the whole corpus every run and cannot be reconciled at all** | |
| 5.4b | A **read-only login** on that database for the dashboard and the reconcilers | `sql/25` DENYs the connector's own writer login SELECT on the crawl views deliberately, so reconciling with the push identity fails by design | |
| 5.5 | A **connection ID** for the Graph connection | Lowercase alphanumeric, fixed for the life of the connection. Changing it later means a new connection and a full re-push | |

## 6 · Network

| # | What we need | Why | Your answer |
|---|---|---|---|
| 6.1 | Firewall opening from the connector host to **SQL Server**, port confirmed | The obvious one, and still worth writing down | |
| 6.2 | Outbound **443** to `login.microsoftonline.com` and `graph.microsoft.com` — from the **agent host** (Path A) or the **push host** (Path B) | Which host needs it is the practical difference between the two paths on a restricted network | |
| 6.3 | Confirmation the **SQL Server certificate is trusted** by the connector host | The connection is encrypted and certificate validation is not disabled | |

---

## Three notes worth reading before you answer

**The deletion question decides the schedule, not the architecture.** It used to
decide the path, on the basis that direct push never detected deletions. It does
now — an inventory diff after a full crawl, a sweep, and a guard that refuses a
sweep after an incremental run — so deletion is bounded by the crawl interval,
and the interval is a setting. What no path offers is immediate removal: if a
record must stop appearing the moment it is deleted, no index qualifies and the
SLA is what has to change.

**A registered schema is append-only (1.7).** No property's type, annotation or
label can be changed after registration. Correcting a mistake means deleting the
connection and every item in it. Fifteen minutes of care over which columns are
searchable and which are filterable is the cheapest fifteen minutes in the
project.

**Please do not attach credentials to your reply (2.3, 4.3, 5.2).** Every row
that touches authentication asks for a *reference* — a secret's name, a
certificate's thumbprint, an account to grant. A parameter request is exactly the
shape of document somebody helpfully attaches a keytab or a password to, and we
would then have to treat it as an incident.

---

*Related: [app registration](APP-REGISTRATION.md) · [hierarchy deployment](HIERARCHY-DEPLOYMENT.md) · [security control mapping](SECURITY.md) · [choosing a path](COPILOT-ROUTING.md)*
