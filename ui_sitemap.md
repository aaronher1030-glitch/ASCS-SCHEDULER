# SCAS UI Sitemap (V1)

## Marketing and Onboarding

- `/` Home (hero, feature cards, request demo CTA)
- `/pricing` Plan tiers for schools/districts
- `/login` Role-based sign in

## App Shell

- `/app/dashboard` tenant overview, active term, build health
- `/app/schools/:schoolId/setup` school profile + trimester template
- `/app/schools/:schoolId/import` SIS/CSV import wizard
- `/app/schools/:schoolId/curriculum` subjects, strands, elective groups
- `/app/schools/:schoolId/teachers` teacher loads and qualifications
- `/app/schools/:schoolId/constraints` policy and constraint profile editor
- `/app/schools/:schoolId/build` build wizard and run panel
- `/app/schools/:schoolId/build/:jobId` live job status and diagnostics
- `/app/schools/:schoolId/conflicts/:versionId` conflict center
- `/app/schools/:schoolId/timetable/:versionId` drag-drop review board
- `/app/schools/:schoolId/student-choice` student elective window controls
- `/app/schools/:schoolId/reports` exports and analytics
- `/app/schools/:schoolId/audit` change logs

## Reusable Components

- `TopNav`, `RoleAwareSidebar`, `SchoolSwitcher`
- `BuildKpiCards`, `BuildStatusTimeline`, `ConflictTable`
- `ConstraintToggleMatrix`, `SectionEditorGrid`, `TeacherLoadTable`
- `TimetableGrid`, `RoomLegend`, `DiffComparePanel`
- `StudentChoiceWindowCard`, `ApprovalQueueTable`
