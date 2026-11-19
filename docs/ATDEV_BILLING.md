# AtDev Billing — Hybrid plans (MemeCode)

**Status:** proposal only. The open-source agent, local execution, and user-controlled approval workflow remain free.

## Hybrid model

Do not charge for reading/editing a local workspace, local review, or local execution. Optional paid services may include AtDev-hosted agent compute, managed model/API access, team workspaces, or hosted task history. Local providers and user-supplied model endpoints must remain supported where practical.

## Proposed plans (CLP/month; exploratory)

| Plan | Reference price | Scope |
| --- | ---: | --- |
| Local / Community | $0 | Local agent workflow and user-configured providers |
| Agent Starter | $490 | Small metered hosted-agent allowance, if launched |
| Agent Plus | $990 | Larger allowance and hosted task history |
| Developer | $1,990 | Higher metered allowance and team conveniences |

Never promise unlimited agent execution. Enforce request, token, runtime, and spending ceilings on the server. Clearly disclose when code or prompts leave the device.

## Suggested entitlements

- `memecode.hosted_agent.requests.monthly`
- `memecode.hosted_agent.runtime_minutes.monthly`
- `memecode.history.hosted_retention_days`
- `memecode.team.seats`

Billing outages must not disable local workflows. No real-money checkout is active; an adult account owner must review provider eligibility and legal/tax obligations before launch.
