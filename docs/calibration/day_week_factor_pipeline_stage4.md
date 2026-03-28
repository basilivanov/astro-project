# Stage 4 calibration entrypoints

- Weight tables live in `backend/app/services/aggregation_weights.py` and use `v2` profile tables.
- Reliability analytics hooks surface via `explainability.reliability_support` in day/week payloads.
- Personal susceptibility scaffolding is stored in `users.susceptibility_profile` and resolved by `backend/app/services/personal_susceptibility.py`.
- Deterministic defaults stay active until `report_feedback` or admin trace review starts writing user-specific multipliers.
- Future loop: convert feedback and trace outcomes into updated domain/category multipliers.
