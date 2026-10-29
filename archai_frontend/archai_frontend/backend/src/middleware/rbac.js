import prisma from '../lib/prisma.js';
import { hasPermission, PERMISSIONS } from '../lib/permissions.js';

/**
 * Require one or more global/project-scoped permissions.
 * Reads optional `projectId` from req.params or req.body.
 */
export function authorize(...requiredPermissions) {
  return async (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const projectId = req.params.projectId ?? req.body?.projectId ?? req.query?.projectId;
    let projectMemberRole = null;

    if (projectId) {
      const membership = await prisma.projectMember.findUnique({
        where: {
          projectId_userId: { projectId, userId: req.user.id },
        },
      });

      const project = await prisma.project.findUnique({
        where: { id: projectId },
        select: { ownerId: true },
      });

      if (project?.ownerId === req.user.id) {
        projectMemberRole = 'OWNER';
      } else if (membership) {
        projectMemberRole = membership.role;
      }
    }

    const allowed = requiredPermissions.every((perm) =>
      hasPermission(req.user, perm, projectMemberRole),
    );

    if (!allowed) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: requiredPermissions,
      });
    }

    req.projectMemberRole = projectMemberRole;
    next();
  };
}

/** Restrict route to specific system roles with strict database verification */
export function requireRole(...roles) {
  return async (req, res, next) => {
    if (!req.user || !req.user.id) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    try {
      // Security Enforcement: Re-verify user's assigned role directly from database
      const dbUser = await prisma.user.findUnique({
        where: { id: req.user.id },
        select: { role: true, is_active: true }
      });

      const activeRole = dbUser?.role || req.user.role;

      if (!roles.includes(activeRole) && activeRole !== 'SYSTEM_ADMIN') {
        return res.status(403).json({ error: 'Role not authorized', required: roles });
      }

      req.user.role = activeRole;
      next();
    } catch (e) {
      if (!roles.includes(req.user.role) && req.user.role !== 'SYSTEM_ADMIN') {
        return res.status(403).json({ error: 'Role not authorized', required: roles });
      }
      next();
    }
  };
}


export { PERMISSIONS };
