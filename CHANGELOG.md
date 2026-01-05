# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Email verification system for users
  - New `email_verificado` field in `Usuario` model to track email verification status (boolean, default: false)
  - New `fecha_verificacion_email` field in `Usuario` model to record verification date (datetime, nullable)
  - Global configuration option `permitir_acceso_email_no_verificado` to allow administrators to enable/disable restricted access for users with unverified emails (boolean, default: false)
  - Warning flash message displayed to users with unverified emails when restricted access is enabled
  - Admin interface in global configuration page to configure restricted access for unverified email users
  - Flask-Migrate integration for database migrations

### Changed
- Login flow now validates email verification status based on global configuration
  - If restricted access is disabled (default), users with unverified emails cannot log in
  - If restricted access is enabled, users can log in with unverified emails but see a warning message
  - Verified users can always log in without restrictions

### Migration Required
⚠️ **IMPORTANT**: This release requires running database migrations.

#### For New Installations
The database schema includes the new fields automatically when you run:

```bash
flask db init
flask db migrate
flask db upgrade
```

#### For Existing Installations  
After updating to this version, you must run the following command to apply database schema changes:

```bash
flask db upgrade
```

Or using payrollctl:

```bash
payrollctl database upgrade
```

The migration adds:
- `email_verificado` column (boolean, not null, default: false) to `usuario` table
- `fecha_verificacion_email` column (datetime, nullable) to `usuario` table  
- `permitir_acceso_email_no_verificado` column (boolean, not null, default: false) to `configuracion_global` table

### Security
- Enhanced security by adding email verification requirement (can be configured by administrators)
- Administrators can control whether unverified users have restricted access to the system
- All existing users will have `email_verificado = false` after migration, requiring email verification unless restricted access is enabled

### Testing
- Comprehensive test coverage with 8 new tests covering:
  - User with verified email can login
  - User with unverified email blocked by default
  - User with unverified email allowed when configured
  - Configuration page shows restricted access option
  - Admin can enable/disable restricted access
  - Model fields are properly accessible
- All existing authentication tests continue to pass (7 tests)
