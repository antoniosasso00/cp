# 📂 Project Structure Snapshot

Root: `C:\Users\Anton\Documents\CarbonPilot`

```
.
├── 2L_BUGS_FIXED_SUMMARY.md
├── 2L_NESTING_FIX_SUMMARY.md
├── CORREZIONI_2L_RIEPILOGO.md
├── CarbonPilot.git
│   ├── HEAD
│   ├── config
│   ├── description
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── fsmonitor-watchman.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── pre-merge-commit.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── push-to-checkout.sample
│   │   ├── sendemail-validate.sample
│   │   └── update.sample
│   ├── info
│   │   └── exclude
│   ├── objects
│   │   └── pack
│   │       ├── pack-fd18648a7a5e327b7029eebf8949950b1c2ec340.idx
│   │       ├── pack-fd18648a7a5e327b7029eebf8949950b1c2ec340.pack
│   │       └── pack-fd18648a7a5e327b7029eebf8949950b1c2ec340.rev
│   └── packed-refs
├── CursorNotes
│   ├── API_v1_Removal_Summary.md
│   ├── Backend_Frontend_v1_Removal_Complete.md
│   ├── NESTING_SEED_GUIDE.md
│   ├── SIDEBAR_STANDARDIZZAZIONE.md
│   ├── batch-nesting-state-transitions.md
│   ├── centralizzazione-costanti.md
│   ├── esempio-utilizzo-costanti.md
│   ├── form-standardization-final.md
│   ├── form-standardization-progress.md
│   ├── frontend-nesting-routing-fix.md
│   ├── nesting-analysis-completa.md
│   ├── nesting-cleanup-summary.md
│   ├── nesting-flow-reorganization.md
│   ├── nesting-multi-batch-ui.md
│   ├── refactoring-app-modules.md
│   ├── riorganizzazione-modulare.md
│   ├── runtime-fixes.md
│   └── sidebar-refactor.md
├── FINAL_INTEGRATION_STATUS.md
├── NESTING_COMPATIBILITY_REPORT.md
├── analyze_2l_data.py
├── analyze_2l_dataset.py
├── backend
│   ├── Dockerfile
│   ├── MODULARIZATION_ISSUE_RESOLUTION.md
│   ├── MODULARIZATION_SUCCESS.md
│   ├── MODULAR_COMPARISON.md
│   ├── PROMPT_6_COMPLETION_REPORT.md
│   ├── REFACTOR_BATCH_NESTING.md
│   ├── VERIFICA_FINALE_2L.md
│   ├── __init__.py
│   ├── alembic
│   │   └── versions
│   │       ├── add_nesting_improvements.py
│   │       ├── add_nesting_result_table.py
│   │       ├── add_odl_model.py
│   │       ├── add_schedule_entry_table.py
│   │       ├── add_standard_times_and_odl_flag.py
│   │       ├── add_system_logs_table.py
│   │       ├── remove_in_manutenzione_and_reparto_fields.py
│   │       └── remove_second_plane_columns.py
│   ├── alembic.ini
│   ├── api
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── routers
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── autoclave.py
│   │   │   ├── batch_modular.py
│   │   │   ├── batch_nesting_modules
│   │   │   │   ├── FIXES_APPLIED.md
│   │   │   │   ├── README.md
│   │   │   │   ├── __init__.py
│   │   │   │   ├── crud.py
│   │   │   │   ├── draft.py
│   │   │   │   ├── generation.py
│   │   │   │   ├── maintenance.py
│   │   │   │   ├── results.py
│   │   │   │   ├── utils.py
│   │   │   │   └── workflow.py
│   │   │   ├── catalogo.py
│   │   │   ├── ciclo_cura.py
│   │   │   ├── dashboard.py
│   │   │   ├── nesting_result.py
│   │   │   ├── odl.py
│   │   │   ├── odl_monitoring.py
│   │   │   ├── parte.py
│   │   │   ├── produzione.py
│   │   │   ├── reports.py
│   │   │   ├── schedule.py
│   │   │   ├── standard_time.py
│   │   │   ├── system_logs.py
│   │   │   ├── tempo_fasi.py
│   │   │   └── tool.py
│   │   └── routes.py
│   ├── apply_2l_migration.py
│   ├── carbonpilot.db
│   ├── logs
│   │   └── nightly_std_update.log
│   ├── main.py
│   ├── migrations
│   │   ├── 20241223_simplify_batch_states.py
│   │   ├── 20250113_170500_add_autoclave_cavalletti_properties.py
│   │   ├── 20250113_add_cavalletti_table.py
│   │   ├── 20250115_add_autoclave_2l_columns.py
│   │   ├── README
│   │   ├── __init__.py
│   │   ├── add_in_coda_status.py
│   │   ├── add_preparazione_to_tempo_fase.py
│   │   ├── add_previous_status_to_odl.py
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   ├── update_nesting_states.py
│   │   └── versions
│   │       ├── 20250127_add_batch_nesting_table.py
│   │       ├── 20250127_add_missing_batch_columns.py
│   │       ├── 20250127_simplify_batch_states.py
│   │       ├── 20250128_add_efficiency_to_batch_nesting.py
│   │       ├── 20250524_182522_init_clean.py
│   │       ├── 20250526_114254_add_two_level_nesting_fields.py
│   │       ├── 20250526_125334_add_system_logs_table.py
│   │       ├── 20250527_add_use_secondary_plane.py
│   │       ├── 20250602_205543_merge_heads.py
│   │       ├── 20250607_204940_add_numero_odl_field.py
│   │       ├── 20250613_143457_add_2l_nesting_support_to_autoclavi.py
│   │       └── add_cavalletto_dimensions_to_autoclavi.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── associations.py
│   │   ├── autoclave.py
│   │   ├── base.py
│   │   ├── batch_history.py
│   │   ├── batch_nesting.py
│   │   ├── catalogo.py
│   │   ├── cavalletto.py
│   │   ├── ciclo_cura.py
│   │   ├── db.py
│   │   ├── nesting_result.py
│   │   ├── odl.py
│   │   ├── odl_log.py
│   │   ├── parte.py
│   │   ├── report.py
│   │   ├── schedule_entry.py
│   │   ├── standard_time.py
│   │   ├── state_log.py
│   │   ├── system_log.py
│   │   ├── tempo_fase.py
│   │   ├── tempo_produzione.py
│   │   ├── tool.py
│   │   └── tool_simple.py
│   ├── nesting_2l_example_output.json
│   ├── reports
│   │   └── generated
│   │       └── report_nesting_20250526_1445.pdf
│   ├── requirements.txt
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── autoclave.py
│   │   ├── batch_nesting.py
│   │   ├── catalogo.py
│   │   ├── ciclo_cura.py
│   │   ├── odl.py
│   │   ├── odl_alerts.py
│   │   ├── odl_monitoring.py
│   │   ├── parte.py
│   │   ├── produzione.py
│   │   ├── reports.py
│   │   ├── schedule.py
│   │   ├── system_log.py
│   │   ├── tempo_fase.py
│   │   └── tool.py
│   ├── scripts
│   │   ├── carbonpilot.db
│   │   ├── refactor_batch_nesting.py
│   │   ├── seed_aeronautico.py
│   │   ├── stress_test_nesting.py
│   │   └── verify_seed.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── auto_report_service.py
│   │   ├── batch
│   │   │   ├── __init__.py
│   │   │   ├── batch_service.py
│   │   │   └── log.py
│   │   ├── nesting
│   │   │   ├── __init__.py
│   │   │   ├── docs
│   │   │   │   ├── COMPLETION_REPORT.md
│   │   │   │   ├── README_solver_2l.md
│   │   │   │   ├── cavalletti_positioning_guide.md
│   │   │   │   └── prompt5_report.md
│   │   │   ├── performance_optimizer.py
│   │   │   ├── solver.py
│   │   │   ├── solver_2l.py
│   │   │   ├── test_schemas_2l.py
│   │   │   └── tests
│   │   │       ├── esempio_cavalletti_manuale.py
│   │   │       ├── final_test_2l.py
│   │   │       ├── simple_test_2l.py
│   │   │       ├── syntax_check_2l.py
│   │   │       ├── test_cavalletti_positioning.py
│   │   │       └── test_solver_2l.py
│   │   ├── nesting_service.py
│   │   ├── odl_alerts_service.py
│   │   ├── odl_log_service.py
│   │   ├── odl_monitoring_service.py
│   │   ├── odl_queue_service.py
│   │   ├── report_service.py
│   │   ├── schedule_service.py
│   │   ├── standard_time_service.py
│   │   ├── state_tracking_service.py
│   │   └── system_log_service.py
│   ├── test_api_call.py
│   ├── test_endpoint_2l.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   └── test_catalogo.py
│   │   ├── conftest.py
│   │   ├── seed_efficiency_test.py
│   │   └── validation_test.py
│   └── utils
│       └── batch
│           ├── __init__.py
│           └── batch_utils.py
├── carbonpilot.db
├── check_and_fix_autoclavi.py
├── check_batch_details.py
├── debug_api_format.py
├── docker-compose.yml
├── docs
│   └── nesting-ux-improvements.md
├── final_integration_test.py
├── frontend
│   ├── Dockerfile
│   ├── NESTING_NOMENCLATURE_GUIDE.md
│   ├── NESTING_WORKFLOW_GUIDE.md
│   ├── batch_nesting_BACKUP.txt
│   ├── next-env.d.ts
│   ├── next.config.js
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   │   └── modules
│   │       └── nesting
│   │           └── result
│   │               └── batch_id
│   ├── src
│   │   ├── app
│   │   │   ├── api
│   │   │   │   └── batch_nesting
│   │   │   │       ├── 2l
│   │   │   │       │   └── route.ts
│   │   │   │       ├── 2l-multi
│   │   │   │       │   └── route.ts
│   │   │   │       └── status
│   │   │   │           └── [jobId]
│   │   │   │               └── route.ts
│   │   │   ├── autoclavi
│   │   │   │   └── page.tsx
│   │   │   ├── catalogo
│   │   │   │   └── page.tsx
│   │   │   ├── dashboard
│   │   │   │   ├── admin
│   │   │   │   │   └── impostazioni
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── clean-room
│   │   │   │   │   ├── produzione
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── tempi
│   │   │   │   │   │   └── components
│   │   │   │   │   │       └── tempo-fase-modal.tsx
│   │   │   │   │   └── tools
│   │   │   │   │       ├── components
│   │   │   │   │       │   └── tool-modal.tsx
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── curing
│   │   │   │   │   ├── batch-monitoring
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── cicli-cura
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── conferma-cura
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── nesting
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   └── result
│   │   │   │   │   │       └── [batch_id]
│   │   │   │   │   │           └── page.tsx
│   │   │   │   │   └── statistics
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── management
│   │   │   │   │   ├── logs
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── monitoraggio
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── monitoraggio
│   │   │   │   │   ├── components
│   │   │   │   │   │   ├── performance-generale.tsx
│   │   │   │   │   │   ├── statistiche-catalogo.tsx
│   │   │   │   │   │   └── tempi-odl.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   ├── modules
│   │   │   │   ├── admin
│   │   │   │   │   └── system-logs
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── autoclavi
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── batch
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── catalogo
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── dashboard
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── nesting
│   │   │   │   │   └── result
│   │   │   │   │       └── [batch_id]
│   │   │   │   │           └── page.tsx
│   │   │   │   ├── odl
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── parti
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── report
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── role
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── schedule
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── tempi
│   │   │   │   │   └── page.tsx
│   │   │   │   └── tools
│   │   │   │       └── page.tsx
│   │   │   ├── nesting
│   │   │   │   ├── list
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   ├── result
│   │   │   │   │   └── [batch_id]
│   │   │   │   │       └── page.tsx
│   │   │   │   └── test-2l
│   │   │   ├── odl
│   │   │   │   ├── [id]
│   │   │   │   │   ├── avanza
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── page.tsx
│   │   │   ├── parti
│   │   │   │   └── page.tsx
│   │   │   ├── report
│   │   │   │   └── page.tsx
│   │   │   ├── schedule
│   │   │   │   └── page.tsx
│   │   │   ├── tempi
│   │   │   │   └── page.tsx
│   │   │   ├── test-canvas
│   │   │   │   └── page.tsx
│   │   │   └── tools
│   │   │       └── page.tsx
│   │   ├── modules
│   │   │   ├── admin
│   │   │   │   ├── impostazioni
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── logs
│   │   │   │   │   └── page.tsx
│   │   │   │   └── system-logs
│   │   │   │       └── page.tsx
│   │   │   ├── autoclavi
│   │   │   │   ├── components
│   │   │   │   │   └── autoclave-modal.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── batch
│   │   │   │   ├── [id]
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── new
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── catalogo
│   │   │   │   ├── components
│   │   │   │   │   └── catalogo-modal.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── schema.ts
│   │   │   ├── clean-room
│   │   │   │   ├── produzione
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── tempi
│   │   │   │   │   └── components
│   │   │   │   │       └── tempo-fase-modal.tsx
│   │   │   │   └── tools
│   │   │   │       ├── components
│   │   │   │       │   └── tool-modal.tsx
│   │   │   │       └── page.tsx
│   │   │   ├── components
│   │   │   │   └── NestingResult
│   │   │   │       ├── BatchParameters.tsx
│   │   │   │       ├── BatchTabs.tsx
│   │   │   │       ├── HistoryPanel.tsx
│   │   │   │       └── NestingDetailsCard.tsx
│   │   │   ├── curing
│   │   │   │   ├── batch-monitoring
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── cicli-cura
│   │   │   │   │   ├── components
│   │   │   │   │   │   └── ciclo-modal.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── conferma-cura
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── nesting
│   │   │   │   │   └── page.tsx
│   │   │   │   └── statistics
│   │   │   │       └── page.tsx
│   │   │   ├── dashboard
│   │   │   │   ├── monitoraggio
│   │   │   │   │   ├── components
│   │   │   │   │   │   ├── performance-generale.tsx
│   │   │   │   │   │   ├── statistiche-catalogo.tsx
│   │   │   │   │   │   └── tempi-odl.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── home
│   │   │   │   └── page.tsx
│   │   │   ├── management
│   │   │   │   ├── logs
│   │   │   │   │   └── page.tsx
│   │   │   │   └── monitoraggio
│   │   │   │       └── page.tsx
│   │   │   ├── nesting
│   │   │   │   ├── list
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── result
│   │   │   │       └── [batch_id]
│   │   │   │           ├── README-2L-COMPATIBILITY.md
│   │   │   │           ├── components
│   │   │   │           │   ├── BatchStatusControl.tsx
│   │   │   │           │   ├── CompatibilityTest.tsx
│   │   │   │           │   ├── DraftActionDialog.tsx
│   │   │   │           │   ├── ExitPageDialog.tsx
│   │   │   │           │   ├── NestingCanvas.tsx
│   │   │   │           │   └── NestingCanvas2L.tsx
│   │   │   │           ├── mock-data-2l.json
│   │   │   │           ├── page.tsx
│   │   │   │           ├── test-compatibility.tsx
│   │   │   │           ├── test-mock-data.json
│   │   │   │           └── test-summary.tsx
│   │   │   ├── odl
│   │   │   │   ├── README.md
│   │   │   │   ├── [id]
│   │   │   │   │   ├── avanza
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── components
│   │   │   │   │   ├── odl-modal-improved.tsx
│   │   │   │   │   ├── odl-modal.tsx
│   │   │   │   │   └── parte-quick-modal.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── schema.ts
│   │   │   ├── parti
│   │   │   │   ├── components
│   │   │   │   │   ├── ciclo-cura-quick-modal.tsx
│   │   │   │   │   ├── parte-modal.tsx
│   │   │   │   │   ├── smart-catalogo-select.tsx
│   │   │   │   │   ├── smart-ciclo-cura-select.tsx
│   │   │   │   │   ├── smart-tools-select.tsx
│   │   │   │   │   └── tool-quick-modal.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── report
│   │   │   │   └── page.tsx
│   │   │   ├── role
│   │   │   │   └── page.tsx
│   │   │   ├── schedule
│   │   │   │   └── page.tsx
│   │   │   ├── tempi
│   │   │   │   └── page.tsx
│   │   │   └── tools
│   │   │       ├── components
│   │   │       │   └── tool-modal.tsx
│   │   │       ├── page.tsx
│   │   │       └── schema.ts
│   │   └── shared
│   │       ├── components
│   │       │   ├── ApiErrorProvider.tsx
│   │       │   ├── AppSidebarLayout.tsx
│   │       │   ├── BarraAvanzamentoODL.tsx
│   │       │   ├── CalendarSchedule.tsx
│   │       │   ├── RecurringScheduleForm.tsx
│   │       │   ├── RoleGuard.tsx
│   │       │   ├── ScheduleForm.tsx
│   │       │   ├── StandardToastProvider.tsx
│   │       │   ├── TempiPreparazioneMonitor.tsx
│   │       │   ├── ToolStatusBadge.tsx
│   │       │   ├── TopDeltaPanel.tsx
│   │       │   ├── canvas
│   │       │   │   └── CanvasWrapper.tsx
│   │       │   ├── charts
│   │       │   │   ├── LazyBarChart.tsx
│   │       │   │   └── LazyLineChart.tsx
│   │       │   ├── dashboard
│   │       │   │   ├── DashboardAdmin.tsx
│   │       │   │   ├── DashboardCleanRoom.tsx
│   │       │   │   ├── DashboardCuring.tsx
│   │       │   │   ├── DashboardManagement.tsx
│   │       │   │   ├── DashboardShortcuts.tsx
│   │       │   │   ├── KPIBox.tsx
│   │       │   │   ├── NestingStatusCard.tsx
│   │       │   │   ├── ODLHistoryTable.tsx
│   │       │   │   └── ODLHistoryTableLazy.tsx
│   │       │   ├── form
│   │       │   │   ├── FormField.tsx
│   │       │   │   ├── FormSelect.tsx
│   │       │   │   ├── FormWrapper.tsx
│   │       │   │   └── index.ts
│   │       │   ├── providers
│   │       │   │   └── SWRProvider.tsx
│   │       │   ├── tables
│   │       │   │   └── LazyBigTable.tsx
│   │       │   ├── theme-provider.tsx
│   │       │   └── ui
│   │       │       ├── ConnectionHealthChecker.tsx
│   │       │       ├── NestingConfigForm.tsx
│   │       │       ├── OdlProgressBar.tsx
│   │       │       ├── OdlProgressBarTest.tsx
│   │       │       ├── OdlProgressWrapper.tsx
│   │       │       ├── OdlTimelineModal.tsx
│   │       │       ├── README_ODL_Progress.md
│   │       │       ├── accordion.tsx
│   │       │       ├── alert.tsx
│   │       │       ├── badge.tsx
│   │       │       ├── button.tsx
│   │       │       ├── calendar.tsx
│   │       │       ├── card.tsx
│   │       │       ├── checkbox.tsx
│   │       │       ├── collapsible.tsx
│   │       │       ├── confirm-dialog.tsx
│   │       │       ├── date-picker.tsx
│   │       │       ├── dialog.tsx
│   │       │       ├── dropdown-menu.tsx
│   │       │       ├── exit-confirmation-dialog.tsx
│   │       │       ├── form.tsx
│   │       │       ├── generation-progress-bar.tsx
│   │       │       ├── index.ts
│   │       │       ├── input.tsx
│   │       │       ├── label.tsx
│   │       │       ├── modal.tsx
│   │       │       ├── popover.tsx
│   │       │       ├── progress.tsx
│   │       │       ├── safe-select.tsx
│   │       │       ├── select.tsx
│   │       │       ├── separator.tsx
│   │       │       ├── sidebar.tsx
│   │       │       ├── slider.tsx
│   │       │       ├── switch.tsx
│   │       │       ├── table.tsx
│   │       │       ├── tabs.tsx
│   │       │       ├── textarea.tsx
│   │       │       ├── theme-toggle.tsx
│   │       │       ├── toast.tsx
│   │       │       ├── toaster.tsx
│   │       │       ├── tooltip.tsx
│   │       │       ├── use-toast.ts
│   │       │       └── user-menu.tsx
│   │       ├── docs
│   │       │   ├── toast-migration-completed.md
│   │       │   └── toast-migration-guide.md
│   │       ├── hooks
│   │       │   ├── README_draft_lifecycle.md
│   │       │   ├── use-draft-lifecycle.ts
│   │       │   ├── use-navigation-guard.ts
│   │       │   ├── use-standard-toast.ts
│   │       │   ├── useApiErrorHandler.ts
│   │       │   ├── useDashboardAPI.ts
│   │       │   ├── useDashboardKPI.ts
│   │       │   ├── useDebounce.ts
│   │       │   ├── useODLByRole.ts
│   │       │   ├── useToolsWithStatus.ts
│   │       │   └── useUserRole.ts
│   │       ├── lib
│   │       │   ├── api.ts
│   │       │   ├── config.ts
│   │       │   ├── constants.ts
│   │       │   ├── swrConfig.ts
│   │       │   ├── types
│   │       │   │   ├── form.ts
│   │       │   │   └── schedule.ts
│   │       │   └── utils.ts
│   │       ├── services
│   │       │   └── toast-service.ts
│   │       └── types
│   │           └── index.ts
│   ├── tailwind.config.ts
│   ├── test-2l-multi-autoclave.md
│   ├── test-smart-canvas-detection.md
│   ├── tsconfig.json
│   └── tsconfig.tsbuildinfo
├── git_commit_tag_push.bat
├── logs
│   └── flow_map_build.log
├── next.config.js
├── requirements.txt
├── sample_2l_corrected_data.json
├── start_dev_fixed.bat
├── test_2l_bugs_fixed_report.json
├── test_2l_bugs_fixed_verification.py
├── test_2l_corrections_demo.py
├── test_2l_database_complete.py
├── test_2l_debug.py
├── test_2l_endpoint.py
├── test_2l_fixes_verification.py
├── test_2l_http_only.py
├── test_2l_multi.py
├── test_2l_nesting_fix_verification.py
├── test_2l_routing_fix.py
├── test_2l_solo.py
├── test_2l_timeout_fix.py
├── test_2l_weight_fix_verification.py
├── test_autoclave_fix.py
├── test_batch_draft_fix.py
├── test_batch_result_fix.py
├── test_cavalletti_positioning_fix.py
├── test_complete_integration.py
├── test_endpoints_direct.py
├── test_final_2l_complete.py
├── test_fix_verification.py
├── test_frontend_fix.py
├── test_nesting_error.py
├── test_robust_timeout_solution.py
├── test_weight_constraints_analysis.py
├── tools
│   ├── carbonpilot.db
│   ├── complete_nesting_seed.py
│   ├── edge_single.py
│   ├── edge_tests.py
│   ├── final_optimization_report.py
│   ├── print_schema_summary.py
│   ├── schema_summary.txt
│   ├── structure.py
│   ├── test_efficiency_optimization.py
│   ├── test_nesting_optimization.py
│   ├── test_optimization_summary.py
│   ├── test_optimized_defaults.py
│   ├── test_simple_optimized.py
│   └── test_solver_optimization_direct.py
└── verify_batch_dependencies.py
```