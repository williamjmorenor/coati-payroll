# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Added concept-level absence defaults to `Percepcion` and `Deduccion` via `es_inasistencia` and `descontar_pago_inasistencia`.
- Updated payroll concept forms and shared concept UI to configure these absence-default flags.
- Updated concept persistence/audit change detection to store and track the new absence-default flags.
- Updated novelty backend creation/update to apply defaults from the selected concept when absence flags are omitted, while preserving explicit payload values.
- Applied the same absence-default resolution to vacation-generated novelties and demo novelty creation for consistent behavior across entry points.
- Added route-level tests for novelty creation to validate default propagation and explicit override behavior.
- Refactored novelty absence-default resolution into a shared utility module to simplify reuse and enable isolated unit testing.
- Added focused unit tests for absence-default resolution and explicit-form override behavior without requiring full view/bootstrap fixtures.

## [1.1.1] - 2026-02-09

### Changed

- Add absence tracking (absences)

## [1.1.0] - 2026-02-09

### Added

- Added a vacation-to-payroll novelty bridge with UI support to apply approved vacations directly into payroll runs.
- Added accounting/reporting flags for perceptions and deductions to invert postings and control report income presentation.

### Changed

- Added absence flags to novelties and applied unpaid-absence salary discounts with a distinct `salario_neto_inasistencia` formula input.
- Standardized the disability novelty concept code to `DISABILITY` for formula sources.
- Updated accounting voucher generation to honor inverted debit/credit configuration for applicable perceptions and deductions.

### Fixed

- Fixed vacation approvals to validate balances, deduct immediately, and log ledger entries consistently.


## [1.0.6] - 2026-02-09

### Changed

- Refactored modules across CLI, queue drivers, payroll processing, and view layers to align with the active lint/type validation baseline.
- Standardized control-flow patterns, SQLAlchemy boolean predicates, import organization, and variable naming to reduce static-analysis false positives.
- Updated `pylint` configuration with explicit non-critical exclusions used by this codebase and its framework integration points.

### CI

- Added `pylint -j 0 coati_payroll` to `.github/workflows/python-package.yml`.
- Added `dev/lint.sh` to run the full local validation stack (`black`, `ruff`, `flake8`, `pylint`, `mypy`, `pytest`, and `pytest -m validation`).

## [1.0.5] - 2026-02-08

### Changed

- Marked the codebase as `mypy` compliant for the `coati_payroll` package under the current type-checking configuration.
- Integrated `mypy` execution into the CI workflow to enforce type checks on every push and pull request.

## [1.0.4] - 2026-02-08

### Fixed

- Preserved `NominaNovedad` records during payroll recalculation to prevent loss of payroll master data.
- Re-linked preserved novelties to the new recalculated payroll run instead of deleting them with old calculation records.
- Added defensive regression tests to ensure novelties are not deleted in future recalculation changes.

## [1.0.3] - 2026-02-08

### Fixed

- Corrected an error in payrun calculation.

## [1.0.2] - 2026-02-07

### Executive Summary

Release 1.0.2 consolidates refactors across payroll processing, accounting vouchers, and liquidation flows to improve determinism, validation strictness, and operational resilience. It also expands the formula engine safety surface and strengthens queue processing and recovery behavior, with supporting test coverage updates.

### Changed

- Refactored queue processing, accounting voucher generation, and payroll execution for clearer error handling and progress tracking.
- Hardened formula engine evaluation, lookup validation, and rounding utilities to improve determinism and type safety.
- Updated liquidation, interest, and vacation services with tighter workflows and consistent snapshot and policy handling.
- Refined UI flows and planilla export/service behaviors to align with revised validation and state transitions.

### Tests

- Extended unit and integration coverage for formula engine, payroll defensive mechanisms, vouchers, vacations, and routes.

## [1.0.1] - 2026-02-06

### Security

- Hardened production startup checks and configuration validation to prevent insecure deployments.
- Enforced rate limiting and upload size safeguards in production while keeping tests isolated.

### Changed

- Upgraded the data layer and normalized enum persistence for more consistent behavior.
- Improved RBAC, auditing, and workflow handling across payroll, loans, and vacation flows.
- Refined CLI, logging, and bootstrap routines to reduce noise and require explicit schema management.

### Fixed

- Resolved edge cases in payroll calculations, loan handling, and vacation workflows.
- Corrected database initialization and connection handling in Docker/runtime environments.

### Documentation

- Expanded operational guides and documented calculation options and edge cases.

## [1.0.0] - 2026-02-02

### Added

- **Formula Engine**: Complete formula evaluation engine with support for:
  - Progressive tax tables with configurable brackets
  - Conditional steps and calculations
  - Variable assignments and expressions
  - Safe operator evaluation (AST-based)
  - Schema validation and security checks

- **Vacation Management Module**: Full-featured vacation system including:
  - Configurable vacation policies
  - Employee vacation accounts with accrual tracking
  - Vacation requests and approval workflow
  - Vacation ledger for complete audit trail

- **Payroll Engine Refactoring**: Clean architecture implementation with:
  - Domain models (PayrollContext, EmployeeCalculation, CalculationItems)
  - Validators (Planilla, Employee, Period, Currency)
  - Calculators (Salary, Concept, Perception, Deduction, Benefit, ExchangeRate)
  - Processors (Loan, Accumulation, Vacation, Novelty, Accounting)
  - Repositories (Planilla, Employee, Acumulado, Novelty, ExchangeRate, Config)
  - Services (PayrollExecution, EmployeeProcessing, AccountingVoucher)

- **Role-Based Access Control (RBAC)**: Permission system with Admin, HR, and Audit roles

- **Reporting System**: Custom reports with role-based permissions and execution audit

- **Queue System**: Background processing for large payrolls with:
  - Dramatiq + Redis for production
  - Huey + Filesystem for development
  - Automatic backend selection

- **Internationalization (i18n)**: Multi-language support with translation files

- **Company-Employee-Planilla Validation**: Internal control ensuring employees and planillas belong to the same company

- **CLI Tool (payrollctl)**: Command-line interface for:
  - System operations (status, check, info, env)
  - Database management (init, seed, backup, restore, migrate)
  - User management (list, create, disable, reset-password)
  - Cache management (clear, warm, status)
  - Maintenance tasks (cleanup-sessions, cleanup-temp, run-jobs)

### Changed

- **Social Contract Compliance**: Complete refactoring to ensure jurisdiction-agnostic design:
  - All jurisdiction-specific examples renamed to generic identifiers
  - Backward-compatible aliases maintained for migration
  - Clear disclaimers added to all example data
  - Documentation updated to reflect generic nature

- **Schema Editor**: Improved JSON schema editor with proper serialization handling

- **Default Values**: Added disclaimers clarifying that default values are for initial adoption only and do not represent legal rules

### Fixed

- Database initialization issues with orphaned indexes
- JavaScript serialization errors in schema editor template
- MutableDict handling for JSON fields in templates

### Security

- Safe expression evaluation using AST visitor pattern
- Input validation on all formula engine operations
- Role-based access control on all sensitive operations

### Documentation

- Complete README with installation, configuration, and usage guides
- Social Contract defining project scope and responsibilities
- Architecture documentation with directory structure
- API documentation for CLI commands
- Local implementation guides (docs/local_guides/)
