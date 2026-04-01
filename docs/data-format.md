# Data Format

## `result.json` Schema

The generated `result.json` has two top-level keys:

```json
{
  "meta": { ... },
  "data": [ ... ]
}
```

### `meta` Object

| Field | Type | Description |
|---|---|---|
| `update` | string | ISO 8601 timestamp of when the data was generated (Asia/Shanghai timezone) |
| `repo` | string | Repository name (e.g. `"Linux Mainline"`) |
| `branch` | string | Branch analyzed (e.g. `"master"`) |
| `commit` | string | First 12 characters of the latest commit SHA on the branch |

### `data` Array

Each element in the `data` array represents one university, sorted by `(count, lines)` descending:

| Field | Type | Description |
|---|---|---|
| `id` | int | Sequential ID (1-based) |
| `rank` | int | Rank position; universities with the same `count` share the same rank |
| `name` | string | University name, or `"Unknown (domain)"` if unrecognized |
| `domains` | string[] | Email domains associated with this university |
| `university` | object \| null | Raw university record from the domain list, or `null` |
| `count` | int | Total number of patches (commits) contributed |
| `lines` | int | Total lines changed (insertions + deletions) |
| `contributor_count` | int | Number of distinct contributor emails |
| `authors` | object[] | Per-author breakdown, sorted by `count` descending |

### `authors` Array Element

| Field | Type | Description |
|---|---|---|
| `email` | string | Author email address |
| `name` | string | Author display name |
| `count` | int | Number of commits by this author |
| `commits` | object[] | List of commit details |

### `commits` Array Element

| Field | Type | Description |
|---|---|---|
| `commit` | string | Full commit SHA |
| `summary` | string | First line of the commit message |
| `date` | string | ISO 8601 authored date |
| `files` | int | Number of files changed |
| `lines` | string | Change summary (e.g. `"-5/+10"`) |

## Invariants

The following properties always hold for a valid `result.json`:

1. `id` values are sequential from 1 to N
2. Entries are sorted by `(count, lines)` descending
3. Entries with the same `count` have the same `rank`
4. `count` equals the sum of all `authors[].count`
5. `contributor_count` equals `len(authors)`
6. No domain appears in more than one entry
7. No university name appears more than once
8. Authors within each entry are sorted by `count` descending
