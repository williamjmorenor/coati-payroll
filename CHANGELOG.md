# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Email verification system for users
  - New `email_verificado` field in `Usuario` model to track email verification status
  - New `fecha_verificacion_email` field in `Usuario` model to record verification date
  - Global configuration option `permitir_acceso_email_no_verificado` to allow administrators to enable/disable restricted access for users with unverified emails
  - Warning flash message displayed to users with unverified emails when restricted access is enabled
  - Admin interface to configure restricted access for unverified email users in global configuration page

### Changed
- Login flow now validates email verification status based on global configuration
  - If restricted access is disabled (default), users must verify their email before logging in
  - If restricted access is enabled, users can log in with unverified emails but see a warning message

### Migration Required
⚠️ **IMPORTANT**: This release requires running database migrations.

After updating to this version, you must run the following command to apply database schema changes:

```bash
flask db upgrade
```

Or using payrollctl:

```bash
payrollctl database upgrade
```

The migration adds:
- `email_verificado` column (boolean, default: false) to `usuario` table
- `fecha_verificacion_email` column (datetime, nullable) to `usuario` table  
- `permitir_acceso_email_no_verificado` column (boolean, default: false) to `configuracion_global` table

### Security
- Enhanced security by adding email verification requirement (can be configured by administrators)
- Administrators can control whether unverified users have restricted access to the system
