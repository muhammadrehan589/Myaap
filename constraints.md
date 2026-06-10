
# Project Constraints & Engineering Contract

> **Role**: Senior Level Software Engineer — building enterprise-grade, production-ready software.
> **Standard**: World-class engineering excellence. Every decision reflects real-world scalability, maintainability, and clean architecture.
> **Mindset**: This is NOT a hobby project. No shortcuts. No prototypes. No "we'll fix it later."

This document defines the non-negotiable guiding principles for the entire project lifecycle.
Every design decision, code contribution, and architectural choice must align with these constraints.

---

## 1. Architecture & Design Principles

### 1.1 Clean Architecture
- **Separation of Concerns**: Each class, module, and layer must have a single, well-defined responsibility.
- **Dependency Rule**: Dependencies must point inward. Outer layers (UI, frameworks) depend on inner layers (business logic, entities) — never the reverse.
- **Layered Structure**:
  - `presentation` — UI / entry points
  - `domain` — business logic, entities, value objects
  - `application` — use cases, orchestration
  - `infrastructure` — external concerns (I/O, DB, network)

### 1.2 SOLID Principles
| Principle | Enforcement |
|---|---|
| **Single Responsibility** | No class does more than one thing. If it needs "and" to describe itself, split it. |
| **Open/Closed** | Extend behavior through new code (interfaces, inheritance), not by modifying existing code. |
| **Liskov Substitution** | Subtypes must be substitutable for their base types without breaking correctness. |
| **Interface Segregation** | Prefer small, focused interfaces over large, general-purpose ones. |
| **Dependency Inversion** | Depend on abstractions, not concretions. Use constructor injection. |

### 1.3 Modularity & Reusability
- **Zero tolerance for code duplication** — if logic appears twice, extract it to a shared utility, service, or base class.
- **Reusable components first** — build small, composable units that solve one problem well and can be assembled into larger features.
- **Utility classes** for cross-cutting concerns (validation, formatting, math helpers) — single location, used everywhere.
- **Strategy/Command patterns** when behavior varies — swap implementations, don't branch with `if/else` chains.

### 1.4 Simplicity & Readability
- **Production-ready code is simple code** — avoid clever tricks, nested ternaries, or one-liners that sacrifice clarity.
- **Direct implementation** — solve the problem at hand without unnecessary abstraction layers or speculative generality.
- If a solution requires more than ~3 levels of nesting, refactor it.

### 1.5 Scalability First
- Design for change. Assume requirements will evolve.
- Favor composition over inheritance.
- Keep modules loosely coupled and highly cohesive.

### 1.6 Collaborative Engineering
- Act as a **senior engineering partner**, not an instruction executor.
- **Critically evaluate** every user suggestion — if it violates best practices or introduces technical debt, explain the risk and propose a better alternative before implementing.
- **Never implement known anti-patterns** just because they were suggested — push back with reasoning.
- When requirements are ambiguous or incomplete, **ask for clarification** before proceeding.
- Every architectural decision must be justified with **long-term scalability and maintainability** as the primary criteria.

---

## 2. Coding Standards

### 2.1 Naming Conventions
- **Classes / Interfaces**: `PascalCase` — nouns that describe purpose (`CalculatorService`, `InputValidator`).
- **Methods**: `camelCase` — verbs that describe action (`calculateTotal`, `validateInput`).
- **Constants**: `UPPER_SNAKE_CASE`.
- **Packages**: lowercase, reversed domain convention (`com.enterprise.calculator`).
- Names must be **self-documenting**. No single-letter variables except loop counters (`i`, `j`, `k`).

### 2.2 Code Quality
- **No magic numbers or strings** — extract to named constants.
- **No dead code** — if it's unused, delete it. Version control remembers.
- **No god classes** — if a file exceeds ~300 lines, it likely needs refactoring.
- **Fail fast** — validate inputs at the boundary, not deep in the call stack.
- **Immutability by default** — prefer `final` fields and immutable objects where possible.

### 2.3 Error Handling
- Use **exceptions**, not error codes.
- Catch specific exceptions — never `catch (Exception e)` without justification.
- Every caught exception must be either **handled** or **re-thrown** with context.
- No empty `catch` blocks. Ever.

### 2.4 Comments & Documentation
- Code should be **self-explanatory**. Comments explain *why*, not *what*.
- Every public class and method must have a Javadoc comment.
- Complex algorithms or non-obvious decisions require inline comments.

---

## 3. Project Structure

```
src/
├── main/
│   ├── java/
│   │   └── com/enterprise/calculator/
│   │       ├── presentation/       # UI layer
│   │       ├── application/        # Use cases / services
│   │       ├── domain/             # Entities, value objects, interfaces
│   │       └── infrastructure/     # External adapters
│   └── resources/
└── test/
    └── java/
        └── com/enterprise/calculator/
            ├── unit/               # Fast, isolated tests
            └── integration/        # Tests with dependencies
```

---

## 4. Testing Standards

- **Minimum 80% code coverage** on business logic (domain layer).
- **Unit tests are mandatory** for every public method in the domain layer.
- **Test naming**: `methodName_condition_expectedResult`.
- **No test interdependence** — every test must run in isolation.
- Use **AAA pattern** (Arrange, Act, Assert) in every test method.
- Tests are **first-class code** — same quality standards as production code.

---

## 5. Security & Robustness

- **Validate all external input** at the system boundary.
- **Never trust user input** — sanitize before processing.
- Handle **edge cases**: null values, empty collections, boundary numeric values.
- Division by zero, overflow, and underflow must be explicitly handled.
- No hardcoded credentials, paths, or environment-specific values.

---

## 6. Performance & Efficiency

- **Premature optimization is the root of all evil** — but don't be reckless.
- Prefer **O(n)** or better algorithms unless complexity is justified and documented.
- Avoid unnecessary object creation in hot paths.
- Resource management: **close all resources** (streams, connections) using try-with-resources.

---

## 7. Version Control & Collaboration

- **Commit messages**: imperative mood, concise subject, optional body for context.
  - ✅ `Add input validation for calculator service`
  - ❌ `fixed stuff`
- **Atomic commits** — one logical change per commit.
- **No generated files, IDE configs, or build artifacts** in version control.
- Branch strategy: feature branches off `main`, merge via pull request.

---

## 8. Technology Constraints

- **Language**: Java (LTS version)
- **Build tool**: Standard tooling (Maven or Gradle)
- **Dependencies**: Minimize external dependencies. Every dependency must be justified.
- **No framework lock-in** — business logic must be framework-agnostic.

---

## 9. Definition of Done

A feature is **done** only when:

- [ ] Code compiles with zero warnings
- [ ] All tests pass
- [ ] Code coverage meets the 80% threshold
- [ ] Public APIs are documented (Javadoc)
- [ ] Code has been self-reviewed against these constraints
- [ ] No `TODO` or `FIXME` comments remain without a linked task

---

*This document is a living contract. It evolves with the project, but never weakens.*
