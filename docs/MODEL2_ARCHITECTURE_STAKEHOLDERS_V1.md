# Model 2 Architecture Stakeholders v1

Last updated: April 2, 2026

## Current Planning Decision

For the current Q2 planning and design phase, the active key stakeholders are:

- PM lead
- Shivika

That is enough to close the current planning question in the Q2 dashboard.

## Important Nuance

This does not mean Model 2 can eventually be deployed with only business approval.

It means that for the current phase of work:

- the project is still in design and operating-model definition
- the immediate architectural direction can be driven by PM lead and Shivika
- broader enterprise approvals become relevant when the project transitions from planning into authenticated shared-service implementation

## Future Shared-Service Approval Set

Once the project moves from planning into an actual Model 2 build and deployment path, the broader gating stakeholders are expected to include:

1. IT architecture / platform owner
2. InfoSec / AI governance
3. IAM / SSO owner
4. Compliance
5. Data owners for VIR and holdings inputs
6. Procurement / vendor risk, if the enterprise LLM route is not already approved

## Why These Become Relevant Later

### IT architecture / platform owner

Needed for:

- hosting approach
- database choice
- internal app pattern
- environment placement
- operational support model

### InfoSec / AI governance

Needed for:

- LLM provider approval
- data handling posture
- audit expectations
- enterprise AI controls

### IAM / SSO owner

Needed for:

- authenticated user access
- user-to-fund scoping
- identity model

### Compliance

Needed for:

- holdings-data handling
- PM note and memory retention rules
- audit logging expectations
- visibility rules across users

### VIR and holdings data owners

Needed for:

- source-of-truth confirmation
- refresh cadence
- field semantics
- operational reliability of input files

### Procurement / vendor risk

Needed only if the enterprise LLM path is not already approved.

## Practical Rule

Use this as the working rule:

- current planning stakeholders: PM lead and Shivika
- future deployment gatekeepers: IT, InfoSec, IAM, Compliance, data owners, and procurement if needed

## Suggested Decision Statement

For current Q2 planning, PM lead and Shivika are the key stakeholders.
Broader enterprise approval stakeholders will be engaged when the project moves from planning into Model 2 implementation.
