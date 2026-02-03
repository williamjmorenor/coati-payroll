# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## unreleased

### Changed:

 - Removed implicit database initialization during application startup and WSGI bootstrap
 - Schema management is now explicit via CLI commands.
 - Enforced mandatory SECRET_KEY configuration in production to prevent insecure deployments.
 - Normalized environment variable parsing for development and auto-migration flags.
 - Improved logging to avoid duplicated handlers and noisy reload output.
 - Reduced sensitive authentication logging and switched last-login timestamps to UTC.
 - Pinned Python dependencies for reproducible builds and removed unnecessary runtime packages from Docker images.
 - Simplified CI linting rules and injected test-only secrets for stable pipelines.
 - Minor typing fixes and code cleanup across views and i18n helpers.

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
