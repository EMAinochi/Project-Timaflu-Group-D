# Database setup

Use the project schema (klassendiagram):

1. `timaflu_schema.sql` (project root)
2. `timaflu_seed.sql` (project root)

```bash
mysql -u root -p < "../timaflu_schema.sql"
mysql -u root -p < "../timaflu_seed.sql"
```

Database name: **timaflu** (see `.env`).
