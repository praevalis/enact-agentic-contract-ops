import type { components } from './generated/types';

/** Identity contracts derived from the generated OpenAPI schema. */
export type Principal = components['schemas']['PrincipalRead'];
export type AccessToken = components['schemas']['TokenRead'];
export type LoginInput = components['schemas']['LoginCreate'];
export type RegistrationInput = components['schemas']['UserCreate'];
export type OrganizationContext =
    components['schemas']['OrganizationContextRead'];
export type OrganizationMembership =
    components['schemas']['OrganizationMembershipRead'];
export type ValidationIssue = components['schemas']['ValidationIssueRead'];
export type MembershipRole = components['schemas']['MembershipRole'];
export type OrganizationMember =
    components['schemas']['OrganizationMemberRead'];
