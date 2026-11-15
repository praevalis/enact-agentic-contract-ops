import type { MembershipRole } from '../../api/contracts';

interface RoleOption {
    label: string;
    description: string;
    dotClass: string;
    badgeClass: string;
}

export const roleOrder: readonly MembershipRole[] = [
    'administrator',
    'deal_desk',
    'operations_reviewer',
    'auditor',
];

export const roleOptions: Record<MembershipRole, RoleOption> = {
    administrator: {
        label: 'Administrator',
        description: 'Manage organization and access',
        dotClass: 'bg-status-processing',
        badgeClass: 'role-badge-administrator',
    },
    deal_desk: {
        label: 'Deal desk',
        description: 'Work with contract cases',
        dotClass: 'bg-status-success',
        badgeClass: 'role-badge-deal-desk',
    },
    operations_reviewer: {
        label: 'Operations reviewer',
        description: 'Review operational decisions',
        dotClass: 'bg-status-review',
        badgeClass: 'role-badge-operations-reviewer',
    },
    auditor: {
        label: 'Auditor',
        description: 'Inspect evidence and results',
        dotClass: 'bg-secondary-text',
        badgeClass: 'role-badge-auditor',
    },
};
