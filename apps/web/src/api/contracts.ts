import type { components } from './generated/types';

/** Identity contracts derived from the generated OpenAPI schema. */
export type Principal = components['schemas']['PrincipalRead'];
export type AccessToken = components['schemas']['TokenRead'];
export type LoginInput = components['schemas']['LoginCreate'];
export type RegistrationInput = components['schemas']['UserCreate'];
