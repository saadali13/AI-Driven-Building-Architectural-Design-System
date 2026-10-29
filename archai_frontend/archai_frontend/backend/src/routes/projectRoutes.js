import express from 'express';
import crypto from 'crypto';
import prisma from '../lib/prisma.js';
import { authorize } from '../middleware/rbac.js';
import { auditLogger } from '../middleware/auditLogger.js';
import { PERMISSIONS } from '../lib/permissions.js';

const router = express.Router();

// Generate Project Share Link
router.post(
  '/:projectId/share',
  authorize(PERMISSIONS.PROJECT_SHARE),
  auditLogger('SHARE', () => 'ProjectShareLink'),
  async (req, res, next) => {
    try {
      const { projectId } = req.params;
      const { permission = 'VIEW', expiresInDays = 7 } = req.body;

      const token = crypto.randomBytes(32).toString('hex');
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + Number(expiresInDays));

      const shareLink = await prisma.projectShareLink.create({
        data: {
          projectId,
          token,
          permission,
          expiresAt,
          createdById: req.user.id,
        },
      });

      res.status(201).json({
        shareUrl: `${process.env.FRONTEND_URL || 'http://localhost:5173'}/shared/${shareLink.token}`,
        token: shareLink.token,
        expiresAt: shareLink.expiresAt,
        permission: shareLink.permission,
      });
    } catch (error) {
      next(error);
    }
  }
);

// Version Snapshot Restoration / Rollback
router.post(
  '/designs/:designId/snapshots/:version/restore',
  authorize(PERMISSIONS.DESIGN_EDIT),
  auditLogger('RESTORE', () => 'DesignSnapshot'),
  async (req, res, next) => {
    try {
      const { designId, version } = req.params;

      const snapshot = await prisma.designSnapshot.findUnique({
        where: { designId_version: { designId, version: Number(version) } },
      });

      if (!snapshot) {
        return res.status(404).json({ error: 'Snapshot version not found' });
      }

      // Update current active design to snapshot layout
      const updatedDesign = await prisma.design.update({
        where: { id: designId },
        data: {
          floorPlanJson: snapshot.floorPlanJson,
          promptText: snapshot.promptText,
          version: { increment: 1 },
        },
      });

      // Log new snapshot version after restoration
      await prisma.designSnapshot.create({
        data: {
          designId,
          version: updatedDesign.version,
          label: `Restored from version ${version}`,
          promptText: snapshot.promptText,
          floorPlanJson: snapshot.floorPlanJson,
          createdById: req.user.id,
        },
      });

      res.json({
        message: `Design successfully restored to version ${version}`,
        design: updatedDesign,
      });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
