# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2] - 2022-03-11
### Added
- Initial release

## [1.0] - 2022-04-14
### Added
- Parameter for environment in `execute` functions
- Service class for AWS STS
- Service class for AWS Batch

### Changed
- `CloudFormation.describe_stack` now returns a Stack object (before: dictionary)

## [1.1] - 2022-04-14
### Fixed
- Empty all images in an ECR when deleting resources of a Cloudformation stack

## [1.2] - 2023-01-06
### Added
- Class `StepFunctions` to execute state machines

## [2.0] - 2022-07-07
### Changed
- Refactoring of task registry

## [2.0.1] - 2025-07-14
### Changed
- Switch to uv

## [2.0.2] - 2025-07-14
### Changed
- Updates in pyproject.toml
