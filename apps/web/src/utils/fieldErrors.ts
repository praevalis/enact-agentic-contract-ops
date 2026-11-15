/**
 * Maps a validation issue at an exact request location to form copy.
 *
 * @param issues - Structured validation issues supplied by a caller.
 * @param location - Full path to the requested value.
 * @param messages - User-facing copy keyed by stable issue code.
 * @returns Form copy for the first matching issue, if present.
 */
export function fieldError(
    issues:
        | readonly {
              location: readonly (string | number)[];
              code: string;
          }[]
        | undefined,
    location: readonly (string | number)[],
    messages: Readonly<Record<string, string>>,
): string | undefined {
    const issue = issues?.find(
        (issue) =>
            issue.location.length === location.length &&
            issue.location.every((part, index) => part === location[index]),
    );

    return issue ? (messages[issue.code] ?? 'Check this value.') : undefined;
}
