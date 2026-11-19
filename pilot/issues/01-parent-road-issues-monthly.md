<!-- File as: Work item form. Title: "Monthly road issue summary for maintenance planners" -->
### The problem
Maintenance planners can't see how many road issues are found each month, by
type and severity, so crew planning is based on anecdote. Inspection data
exists in Snowflake (ROADWAY_* databases, RAW schema) but was built by hand,
isn't versioned, and nothing reports on it.

### Intended outcome
A monthly summary of approved road issues by issue type and severity, served
from a governed Snowflake mart and shown on one Power BI page, with numbers
that reconcile to the raw inspection data.

### Likely targets
- [x] terraform (adopt the hand-built databases; reporting role for Power BI)
- [x] snowflake (adopt the hand-built view; new monthly mart)
- [x] powerbi (one page)

### Data access
Domain: roadway. PROD profiling requested; link the `terraform/access/roadway.tf` PR when approved.

### Notes and links
Pilot 1 of the AI-DLC multi-stack kit. All data is synthetic.
