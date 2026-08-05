# scripts/ — thin orchestrators

Thin CLIs that coordinate the REMOUNT domain core. One script per mission
phase plus helpers. Each self-bootstraps `src/` onto `sys.path`.

| Script | Phase | Behavior |
| --- | --- | --- |
| `brief.py` | brief | Print the mission brief |
| `recon.py` | recon | Print recon findings (optional goal argv) |
| `plan.py` | plan | Print the plan steps |
| `execute.py` | execute | Run replay→diff→migrate→risk→allocate→forecast; write `output/data/remount_outcome.json` |
| `debrief.py` | debrief | Print outcome success + lessons |
| `run_mission.py` | full | Drive the whole flow via `bond_api.run_mission` |
| `00_preflight.py` | verify | Confirm the provider satisfies the protocol |
| `z_generate_manuscript_variables.py` | hydrate | Resolve `{{TOKEN}}`s + render the four figures |

Convention: signed operation names in `outcome.results` come from the domain
core, never defined here. Business logic lives in `src/`, not in these scripts.
