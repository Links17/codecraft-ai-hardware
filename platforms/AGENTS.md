# Platform rules

Each software stack owns its adapter, Targets, native configuration, tests and simulation. Native peripheral interfaces live in target.json under interfaces; they are not cloud Skill Capabilities.

Adapters implement build, cases, probe and validate_target. Declare all ten operation statuses in platform.json. Use the generic runtime for JSON envelopes and command execution only. Missing tools mean not_run. Exact expected case coverage, Target identity, operation and source digest must match the result. Declare all native source inputs and dependencies, including per-example locks. New stacks need a real reference Target and adapter tests before board support can be claimed.
