import prisma from '../lib/prisma.js';

/**
 * Express Middleware to capture automated audit trails for user actions.
 * Logs action, entity, user ID, timestamp, prompt text, IP, and User Agent to PostgreSQL via Prisma.
 */
export function auditLogger(action, entityTypeExtractor) {
  return async (req, res, next) => {
    const originalJson = res.json;

    res.json = function (body) {
      res.json = originalJson;

      // Process audit log asynchronously
      setImmediate(async () => {
        try {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            const entityType = typeof entityTypeExtractor === 'function' 
              ? entityTypeExtractor(req) 
              : (entityTypeExtractor || 'SYSTEM');

            const entityId = req.params.id || req.body.id || body?.id || null;

            await prisma.auditLog.create({
              data: {
                userId: req.user?.id || null,
                action: action || 'UPDATE',
                entityType: String(entityType),
                entityId: entityId ? String(entityId) : null,
                metadata: {
                  path: req.originalUrl,
                  method: req.method,
                  params: req.params,
                  promptText: req.body?.promptText || req.body?.prompt || undefined,
                },
                ipAddress: req.ip || req.headers['x-forwarded-for'] || null,
                userAgent: req.get('user-agent') || null,
              },
            });
          }
        } catch (err) {
          console.error('[AuditLogger Middleware Exception]:', err.message);
        }
      });

      return res.json(body);
    };

    next();
  };
}
