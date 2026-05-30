# grace-orchestrator Extraction Checklist

## Phase 3: Prepare Extraction Structure ✅ COMPLETED

### Documentation Files ✅
- [x] README.md - Comprehensive project documentation
- [x] LICENSE - MIT License
- [x] MIGRATION.md - Migration guide for existing projects
- [x] CONTRIBUTING.md - Contribution guidelines
- [x] CHANGELOG.md - Version history
- [x] SETUP.md - Detailed setup instructions
- [x] MANIFEST.in - Package manifest

### Docker Files ✅
- [x] docker/Dockerfile.worker - Worker container image
- [x] docker/docker-compose.fragment.yaml - Compose template
- [x] docker/requirements.txt - Python dependencies

### Summary ✅
- [x] PHASE3_SUMMARY.md - Completion summary

## Phase 4: Document Migration Steps (NEXT)

### Migration Documentation
- [ ] Review MIGRATION.md for completeness
- [ ] Add specific examples from astro-project
- [ ] Document edge cases and gotchas
- [ ] Create before/after code snippets
- [ ] Add troubleshooting for astro-project specific issues

### Testing Migration
- [ ] Test migration steps on a copy of astro-project
- [ ] Verify all imports work after migration
- [ ] Ensure Docker setup works
- [ ] Test gracectl commands
- [ ] Validate Prefect integration

### Migration Scripts
- [ ] Create automated migration script (optional)
- [ ] Add validation script to check migration completeness
- [ ] Create rollback script

## Phase 5: Create New Repository (FUTURE)

### Repository Setup
- [ ] Create new GitHub repository: grace-orchestrator
- [ ] Initialize with README.md
- [ ] Add LICENSE
- [ ] Set up branch protection rules
- [ ] Configure GitHub Actions for CI/CD

### File Migration
- [ ] Move documentation files to new repo
- [ ] Move Docker files to new repo
- [ ] Copy gracectl/ directory to src/grace_orchestrator/cli/
- [ ] Copy prefect_grace/ to src/grace_orchestrator/
- [ ] Update all import paths

### Package Structure
- [ ] Create src/grace_orchestrator/ directory structure
- [ ] Create pyproject.toml with package metadata
- [ ] Set up entry points for CLI commands
- [ ] Configure build system (setuptools/hatchling)

### Testing
- [ ] Set up pytest configuration
- [ ] Create test fixtures
- [ ] Write unit tests for core functionality
- [ ] Write integration tests
- [ ] Set up coverage reporting

### CI/CD
- [ ] GitHub Actions workflow for tests
- [ ] GitHub Actions workflow for linting
- [ ] GitHub Actions workflow for publishing to PyPI
- [ ] Pre-commit hooks configuration
- [ ] Dependabot configuration

### Documentation
- [ ] Set up ReadTheDocs or similar
- [ ] Create API documentation
- [ ] Add usage examples
- [ ] Create tutorial series
- [ ] Add architecture diagrams

## Phase 6: Publish Package (FUTURE)

### PyPI Preparation
- [ ] Choose package name (grace-orchestrator)
- [ ] Verify name availability on PyPI
- [ ] Create PyPI account/organization
- [ ] Set up PyPI API tokens

### Package Build
- [ ] Build source distribution (sdist)
- [ ] Build wheel distribution
- [ ] Test installation from built package
- [ ] Verify all files included in distribution

### Publishing
- [ ] Publish to TestPyPI first
- [ ] Test installation from TestPyPI
- [ ] Publish to PyPI
- [ ] Create GitHub release
- [ ] Tag version (v0.1.0)

### Post-Publication
- [ ] Update README badges with PyPI version
- [ ] Announce release
- [ ] Update documentation with installation instructions
- [ ] Monitor for issues

## Phase 7: Migrate astro-project (FUTURE)

### Preparation
- [ ] Create migration branch in astro-project
- [ ] Back up current state
- [ ] Document current GRACE setup

### Migration
- [ ] Install grace-orchestrator package
- [ ] Create grace/ directory structure
- [ ] Migrate gracectl.yaml to grace/project.yaml
- [ ] Create grace/agent_profiles.yaml
- [ ] Update docker-compose.yml
- [ ] Update environment variables

### Code Updates
- [ ] Update all imports from prefect_grace to grace_orchestrator
- [ ] Update all imports from gracectl to grace_orchestrator
- [ ] Remove old prefect_grace/ directory
- [ ] Remove old gracectl/ directory
- [ ] Update CI/CD pipelines

### Testing
- [ ] Run all verification slices
- [ ] Test gracectl commands
- [ ] Verify Docker worker functionality
- [ ] Test Prefect integration
- [ ] Run full test suite

### Cleanup
- [ ] Remove old GRACE implementation files
- [ ] Update .gitignore
- [ ] Update documentation
- [ ] Create migration PR
- [ ] Review and merge

## Current Status

**Phase 3**: ✅ COMPLETED (2026-05-30)
- All documentation files created
- Docker files prepared
- Package manifest ready
- Files ready for new repository

**Phase 4**: 🔄 READY TO START
- Migration documentation needs review
- Testing migration steps needed
- Optional automation scripts

**Next Action**: Review Phase 3 files and begin Phase 4 migration documentation refinement.

## Notes

- All placeholder URLs (yourusername, etc.) need to be updated with actual repository information
- PyPI package name "grace-orchestrator" should be verified for availability
- Consider creating example projects in examples/ directory
- May want to add architecture diagrams to documentation
- Consider creating video tutorials for setup and usage

## File Locations

Current location: `/opt/astro-project/`

Files to move to new repo:
- README.md
- LICENSE
- MIGRATION.md
- CONTRIBUTING.md
- CHANGELOG.md
- SETUP.md
- MANIFEST.in
- docker/Dockerfile.worker
- docker/docker-compose.fragment.yaml
- docker/requirements.txt

Source code to extract:
- gracectl/ → src/grace_orchestrator/cli/
- prefect_grace/ → src/grace_orchestrator/
- infra/grace-worker/ → docker/ (already done)
