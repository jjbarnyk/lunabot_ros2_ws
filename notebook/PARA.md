# PARA — How This Notebook Is Organized

PARA is a note organization system by Tiago Forte. Every piece of information lives in exactly one of four categories, ordered by how actionable it is.

---

## The Four Categories

### 1 - Projects
A project is **work with a specific goal and a deadline** — something that will be done eventually.

Examples here:
- Getting the robot to run autonomously at competition
- Integrating Nav2 with the mission state machine

> Rule: if there's no finish line, it's not a project — it's an area.

---

### 2 - Areas
An area is a **sphere of responsibility you maintain over time** with no end date.

Examples here:
- Motor control (always needs to work)
- Localization (ongoing tuning and maintenance)
- Dashboard

> Rule: areas don't get completed — they get maintained. When a project closes, its notes either go into a relevant area or into archives.

---

### 3 - Resources
Resources are **reference material on topics you care about** — no action required, just useful to look up.

Examples here:
- Hardware parameters and CAN IDs
- Build and run commands
- System architecture diagrams

> Rule: resources are pull-based. You don't act on them; you consult them.

---

### 4 - Archives
Archives hold **inactive items from the other three categories**.

When a project finishes, move it here. When an area is no longer relevant, move it here. Nothing gets deleted — just archived.

> Rule: archive aggressively. A cluttered active workspace is worse than a big archive.

---

## The Key Insight

The categories are ordered by **actionability**:

```
Projects  →  most actionable  (doing this now)
Areas     →  ongoing          (responsible for this)
Resources →  reference        (useful someday)
Archives  →  inactive         (not now)
```

When you pick up a task, start in Projects. When you need context, look in Areas. When you need a fact, look in Resources.

---

## Maintenance Rules

- **Weekly**: check Projects — are they still active? Did anything finish?
- **When starting new work**: create a Project note first.
- **When a project ends**: move the note to Archives or distill key info into an Area.
- **Never nest deeply**: flat is better. One level of folders is enough.
