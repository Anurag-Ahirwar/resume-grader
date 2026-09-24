# Resume Grader — Claude Code Project Instructions

## Autonomous Product Improvement Authority

Claude Code has permission to identify and implement reasonable improvements
that can make Resume Grader more reliable, secure, maintainable, usable,
professional, or production-ready.

Do not limit implementation strictly to the explicitly listed requirements
when a clearly beneficial improvement is discovered during development.

### Claude MAY proactively improve:

- Code quality and architecture
- Error handling
- Input validation
- Security
- Authentication and authorization
- Database integrity
- API consistency
- Frontend UX/UI
- Accessibility
- Performance
- Logging and observability
- Testing and test coverage
- Developer experience
- Documentation
- Configuration management
- Type safety
- Edge-case handling
- Loading/error/empty states
- User feedback and validation messages
- Data consistency
- Maintainability
- Backward compatibility
- Production-readiness

### Examples

If implementing authentication reveals that an endpoint is still publicly
accessible, protect it.

If a form accepts invalid input, add appropriate validation.

If an API endpoint exposes an internal error or stack trace, improve the
error handling.

If a database operation can leave inconsistent records, make it transactional
or otherwise safer.

If a frontend page has an obvious broken loading, empty, or error state,
improve it.

If a security weakness is discovered that is directly related to the current
feature, fix it rather than leaving it knowingly unresolved.

If adding authentication reveals that the existing admin reset endpoint lacks
authorization, secure it.

If tests reveal a bug in existing code that is directly related to the feature
being implemented, fix the bug and add a regression test.

### Scope Rule

Proactive improvements must remain relevant to Resume Grader and the current
task.

Do NOT use this permission to:

- Rewrite unrelated working systems
- Introduce unnecessary frameworks
- Add large features unrelated to the current task
- Replace working architecture merely because another technology is available
- Change product requirements without justification
- Remove existing functionality
- Change scoring rules without explicit product-level justification
- Make subjective product decisions that materially change user behaviour
- Add unnecessary dependencies
- Significantly increase project complexity without a clear benefit

### Decision Rule

For every proactive improvement, ask:

1. Does this directly improve reliability, security, usability,
   maintainability, performance, or production-readiness?
2. Is it reasonably small and contained within the current task?
3. Can it be implemented without breaking existing functionality?
4. Can it be tested?
5. Is the benefit clearly greater than the added complexity?

If YES to all five, implement it autonomously.

If NO, leave it unchanged and report it as a recommendation.

### No Silent Scope Creep

At the end of the task, provide a section:

## Proactive Improvements Made

For every improvement not explicitly requested, report:

- What was changed
- Why it was changed
- Files affected
- How it was tested

Also provide:

## Recommended Future Improvements

List useful improvements discovered during implementation but intentionally
not implemented because they were outside the current scope.

### Priority Rule

When choosing between:

1. implementing a requested feature,
2. fixing a directly related bug,
3. adding a nice-to-have enhancement,

always prioritize:

1. Correctness
2. Security
3. Data integrity
4. Requested functionality
5. Testing
6. UX improvements
7. Performance
8. Nice-to-have enhancements

Never sacrifice correctness or security for a cosmetic improvement.

## Engineering Mindset

Do not treat this project as a collection of isolated tasks.

Understand the existing product, architecture, user workflow, and long-term
direction before making changes.

When implementing a feature, consider its impact on:

- Security
- Data integrity
- Existing functionality
- API contracts
- UX
- Maintainability
- Testing
- Future scalability

Prefer simple, robust solutions over unnecessarily sophisticated ones.

The goal is to leave the repository in a better state than you found it.
