# SCAS Initial ERD (Trimester + SHS Electives)

```mermaid
erDiagram
  Tenant ||--o{ School : owns
  School ||--o{ AcademicYear : has
  AcademicYear ||--o{ Term : contains
  School ||--o{ Program : offers
  Program ||--o{ GradeLevel : has
  GradeLevel ||--o{ Section : contains
  Program ||--o{ Subject : defines
  Subject }o--o{ ElectiveGroup : optionalIn
  School ||--o{ Teacher : employs
  School ||--o{ Room : manages
  Section ||--o{ Student : enrolls
  Student ||--o{ StudentRequest : submits
  Subject ||--o{ StudentRequest : requestedAs
  School ||--o{ ConstraintProfile : configures
  ConstraintProfile ||--o{ ConstraintRule : includes
  School ||--o{ BuildJob : runs
  BuildJob ||--o{ BuildResult : produces
  BuildResult ||--o{ ConflictItem : detects
  BuildResult ||--o{ ScheduleVersion : snapshots
  BuildResult ||--o{ ResolutionAction : records
  School ||--o{ IntegrationConnectorRun : tracks
  School ||--o{ AuditLog : logs
```

## Notes

- `Term` supports trimester and semester setups (`term_index`, `start_date`, `end_date`).
- `ElectiveGroup` allows SHS strand-specific pools with min/max pick counts.
- `StudentRequest` stores ranked elective preferences and approval status.
- `BuildJob` keeps orchestration state while `BuildResult` stores immutable outputs.
