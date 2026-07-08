# Enterprise IdP Federation Runbook

How to federate an HPP Cognito user pool to a customer identity provider so that
**sign-in, group membership, and approver role** are owned by the customer's IdP —
no user accounts are managed in AWS. Covers **Okta** and **Microsoft Entra ID**
(Azure AD), the claim→role mapping the gateway authorizer depends on, and how to
flip federation on/off.

> **What the template does.** The optional addon
> [`infra/cloudformation/idp-federation.yaml`](../infra/cloudformation/idp-federation.yaml)
> provisions: an `AWS::Cognito::UserPoolIdentityProvider` (SAML), an
> `AWS::Cognito::UserPoolDomain` (hosted UI), and a **new federated app client**
> (`SupportedIdentityProviders`, `AllowedOAuthFlows: [code]`, scopes,
> callback/logout URLs) on an **existing** HPP user pool. All of it is gated by
> the CloudFormation Condition **`FederationEnabled`**, which is true only when
> `IdpMetadataUrl` is non-empty. It is a standalone addon on purpose: the
> acceptance-gated golden path (`infra/golden-path-01-revenue-cycle/`) and the
> nested quickstart deploy **unchanged** whether or not this stack exists, and
> the base stacks' native app client is never modified.

---

## 0. The contract the platform depends on

The MCP gateway authorizes deny-by-default entitlement and *who may approve* a
gated write from a single custom claim: **`custom:hpp_role`**
(`platform_core/hpp_agent_platform/auth.py: ROLE_CLAIM_KEYS`; the gateway reads
`AUTH_ROLE_CLAIM`, default `custom:hpp_role`). Federation must map the IdP's
group/role claim into that attribute. The `email` claim is also mapped for audit
identity.

| Cognito attribute  | Sourced from IdP claim       | Used for |
|--------------------|------------------------------|----------|
| `email`            | the IdP email/UPN claim      | audit identity, separation-of-duties (requester ≠ approver) |
| `custom:hpp_role`  | the IdP **group/role** claim | authorization (e.g. `DENIALS_SPECIALIST` may draft, `DENIALS_MANAGER` may approve an appeal) |

The mapping is set in `idp-federation.yaml` (`AttributeMapping`, overridable via
the `IdpEmailClaim` / `IdpRoleClaim` parameters) for the common SAML claim URIs,
and can also be adjusted in the Cognito console per IdP if the customer emits
non-standard claim names. Both HPP pools (`infra/cloudformation/security.yaml`
and the golden-path template) already define the `custom:hpp_role` schema
attribute.

---

## 1. Stack parameters

Deploy the addon against the pool you already stood up:

```bash
aws cloudformation deploy --template-file infra/cloudformation/idp-federation.yaml \
  --stack-name hpp-01-revenue-cycle-denial-dev-idp \
  --parameter-overrides \
      AgentId=01-revenue-cycle-denial Environment=dev \
      UserPoolId=<UserPoolId output of security.yaml or the golden path> \
      IdpMetadataUrl="https://<tenant>.okta.com/app/<id>/sso/saml/metadata" \
      CallbackUrl="https://reviewer.acme.example/callback" \
      UserPoolDomainPrefix=acme-hpp-dev
```

| Parameter              | Example                                                | Notes |
|------------------------|--------------------------------------------------------|-------|
| `UserPoolId`           | `us-east-1_AbCdEfGhI`                                  | The existing HPP pool to federate (stack output `UserPoolId`). |
| `IdpMetadataUrl`       | `https://<tenant>.okta.com/app/<id>/sso/saml/metadata` | **Non-empty turns federation ON.** Empty = the stack creates nothing (safe no-op). |
| `CallbackUrl`          | `https://reviewer.acme.example/callback`               | OAuth redirect URL registered on the federated app client (and used as logout URL). |
| `UserPoolDomainPrefix` | `acme-hpp-prod`                                        | Hosted-UI domain label; globally unique per Region. Empty = deterministic default. |
| `IdpEmailClaim` / `IdpRoleClaim` | *(defaults cover standard SAML URIs)*        | Override when the IdP emits non-standard claim names. |

---

## 2. Okta (SAML)

1. **Okta Admin → Applications → Create App Integration → SAML 2.0.**
2. **Single sign-on URL / Audience (SP entity ID).** You need the Cognito values,
   which depend on the hosted-UI domain you chose:
   - **ACS URL:** `https://<UserPoolDomainPrefix>.auth.<region>.amazoncognito.com/saml2/idpresponse`
   - **Audience URI (SP entity ID):** `urn:amazon:cognito:sp:<UserPoolId>`
   (Get `<UserPoolId>` from the base stack output `UserPoolId`; the domain from
   the addon output `HostedUiDomain`.)
3. **Attribute Statements** — emit at minimum:
   - `email` → `user.email`
   - a **group claim**: add a **Group Attribute Statement** named e.g. `Group`
     filtered to the revenue-cycle / clinical groups (e.g. regex `GRP-RCM-.*`).
4. **Assign** the relevant Okta groups (e.g. `GRP-RCM-DENIALS-MANAGERS`) to the app.
5. **Copy the Okta IdP metadata URL** (Sign-On tab → *Identity Provider metadata*).
   This is your `IdpMetadataUrl`.
6. **Map the group → role.** The addon's default `IdpRoleClaim`
   (`http://schemas.xmlsoap.org/claims/Group`) maps the SAML `Group` claim to
   `custom:hpp_role`. If your group names are not the literal role strings the
   policy expects (`DENIALS_SPECIALIST`, `DENIALS_MANAGER`, `UM_NURSE`, …), use
   an Okta **expression** in the attribute statement to emit the role string
   directly (e.g. `isMemberOfGroupName("GRP-RCM-DENIALS-MANAGERS") ? "DENIALS_MANAGER" : ""`).

---

## 3. Microsoft Entra ID (Azure AD) (SAML)

1. **Entra admin center → Enterprise applications → New application → Create your
   own application → "Integrate any other application (non-gallery)".**
2. **Single sign-on → SAML.** Set:
   - **Identifier (Entity ID):** `urn:amazon:cognito:sp:<UserPoolId>`
   - **Reply URL (ACS):** `https://<UserPoolDomainPrefix>.auth.<region>.amazoncognito.com/saml2/idpresponse`
3. **Attributes & Claims:**
   - Ensure `email` (or `user.mail` / `user.userprincipalname`) is emitted as the
     email claim.
   - Add a **group claim** (Token configuration → *groups claim* → "Groups assigned
     to the application"). Entra emits group **object IDs** by default; to emit
     names, either configure the app to surface group names or use a Cognito
     mapping that translates the known group GUID → role downstream.
4. **Users and groups:** assign the reviewer/approver groups to the application.
5. **App Federation Metadata URL** (on the SAML SSO page) → this is your
   `IdpMetadataUrl`.
6. **Map the group claim → `custom:hpp_role`**, exactly as in §2.6. Because Entra
   emits GUIDs, the cleanest pattern is an **Entra claims-transformation** that
   emits the literal role string (e.g. `DENIALS_MANAGER`) for members of the
   approver group, so `custom:hpp_role` carries the role directly.

---

## 4. OIDC alternative

OIDC is accepted instead of SAML. In `idp-federation.yaml` change the
`CustomerIdentityProvider` resource:

```yaml
ProviderType: OIDC
ProviderDetails:
  client_id: "<oidc-app-client-id>"
  client_secret: "<oidc-app-client-secret>"
  oidc_issuer: "https://<issuer>"
  attributes_request_method: GET
  authorize_scopes: "openid email profile groups"
AttributeMapping:
  email: email
  "custom:hpp_role": groups
```

`IdpMetadataUrl` still gates `FederationEnabled`; you can leave it non-empty (e.g.
the issuer's `.well-known` URL) to keep the condition on, or refactor the condition
to a dedicated `FederationEnabled` boolean parameter for OIDC-only deployments.

---

## 5. Wiring the gateway to accept federated tokens

The portable gateway's JWT authorizer validates **issuer + audience**. The
issuer is unchanged (same user pool), but the federated app client is a **new
audience**: add the addon output `FederatedClientId` to the authorizer's
audience list —

- **Golden path** (`infra/golden-path-01-revenue-cycle/template.yaml`): the
  `HttpApi` `CognitoJwt` authorizer `audience: [...]`.
- **Quickstart** (`infra/cloudformation/gateway-portable.yaml`): the JWT
  authorizer's audience parameter/property.
- **Reference gateway** (`platform_core`): the `JWT_AUDIENCE` env the verifier
  checks.

Without this, federated logins succeed but the gateway rejects the token
(`aud` mismatch) — deny-by-default working as intended.

---

## 6. Flipping federation on / off

- **ON:** deploy the addon with a non-empty `IdpMetadataUrl` (+
  `UserPoolDomainPrefix` and a real `CallbackUrl`). The `FederationEnabled`
  condition provisions the IdP, the hosted-UI domain, and the federated app
  client. Stack output `FederationEnabled` reads `true` and `HostedUiDomain`
  shows the sign-in domain.
- **OFF (dev / native Cognito):** don't deploy the addon at all — or deploy it
  with `IdpMetadataUrl=""` (default), which creates nothing. The base stacks
  never change either way.
- **Removing federation from a live stack** is a normal stack delete of the
  addon (the base pool and its native client are untouched). Plan the cutover
  with the customer (existing native users vs. federated users).

---

## 7. Verify

1. Addon stack output `FederationEnabled == true`, `HostedUiDomain` set.
2. Navigate to the hosted UI:
   `https://<HostedUiDomain>.auth.<region>.amazoncognito.com/login?client_id=<FederatedClientId>&response_type=code&scope=openid+email+profile&redirect_uri=<CallbackUrl>`
   → you should be redirected to the customer IdP, authenticate, and land back at
   `CallbackUrl` with a `code`.
3. Exchange the code for tokens and decode the ID token: confirm `email` and
   **`custom:hpp_role`** are present and correct. The gateway authorizer reads
   `custom:hpp_role`; an empty/wrong value = deny on entitlement/approval.

> **Live-account note.** The end-to-end federated login (steps 2–3) and the
> claim→role assertion can only be confirmed against a real Cognito pool + IdP.
> This runbook + the cfn-lint-clean template are validated structurally; the
> live federated-login leg is customer-engagement work (see the maturity matrix
> in `README.md` and `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`).
