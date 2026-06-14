You are a security and compliance reviewer.

Read the snap-forge repo docs.

Threat model the first build spike:

QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> staff/customer notification.

Focus on:
- RLS bypass
- service_role misuse
- SECURITY DEFINER risks
- approval-gate bypass
- audit log integrity
- idempotency
- prompt injection and excessive AI agency
- outbound SMS/email risk
- future HIPAA/PCI/Metrc implications

Return concrete controls, test cases, and CI/static checks.
Use primary sources where possible.

Separate:
- confirmed public evidence
- partner/private verification required
- settle-by-building
