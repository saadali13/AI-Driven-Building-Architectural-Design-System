import { syncProjectToSupabase } from '../lib/supabase';
import { apiService } from '../services/apiService';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Project, DesignAlternative, DesignTemplate, MaterialRateItem, CostEstimate, AppNotification, AuditLog, RoomSpec, BuildingType, PlotPreset, ArchitecturalStyle, PlotUnit } from '../types';
import {
  INITIAL_PROJECTS,
  MOCK_TEMPLATES,
  MOCK_MATERIAL_RATES,
  INITIAL_COST_ESTIMATES,
  INITIAL_NOTIFICATIONS,
  INITIAL_AUDIT_LOGS,
} from '../data/mockData';
import { calculatePreliminaryCost } from '../services/costEstimatorService';

interface ProjectContextType {
  projects: Project[];
  templates: DesignTemplate[];
  materialRates: MaterialRateItem[];
  costEstimates: CostEstimate[];
  notifications: AppNotification[];
  auditLogs: AuditLog[];
  isGenerating: boolean;
  generationPhase: string;
  generationProgress: number; // 0 to 100
  getProjectById: (id: string) => Project | undefined;
  createProject: (newProject: Omit<Project, 'id' | 'createdAt' | 'updatedAt' | 'designAlternatives'>) => Project;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
  duplicateProject: (id: string) => Project;
  toggleFavoriteProject: (id: string) => void;
  toggleFavoriteTemplate: (id: string) => void;
  generateDesignAlternative: (projectIdOrProject: string | Project, userNotes?: string) => Promise<DesignAlternative>;
  addCostEstimate: (estimate: CostEstimate) => void;
  updateMaterialRate: (id: string, newRate: number) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  resetDemoData: () => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const PROJECTS_STORAGE_KEY = 'archicraft_projects_state';

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>(() => {
    try {
      const saved = localStorage.getItem(PROJECTS_STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch {
      // fallback
    }
    return INITIAL_PROJECTS;
  });

  // Sync projects from backend database on mount
  useEffect(() => {
    apiService.getProjects()
      .then((backendProjects) => {
        if (backendProjects && backendProjects.length > 0) {
          setProjects((prev) => {
            const existingIds = new Set(prev.map(p => p.id));
            const formatted = backendProjects.map((bp: any) => ({
              id: bp.id || bp.project_id || `proj_${Date.now()}`,
              title: bp.name || bp.title || 'Architectural Project',
              type: (bp.type || 'House') as BuildingType,
              ownerId: bp.ownerId || 'usr_customer_1',
              ownerName: bp.ownerName || 'Homeowner',
              plotPreset: (bp.plot_size?.toLowerCase()?.includes('5') ? '5_marla' : bp.plot_size?.toLowerCase()?.includes('10') ? '10_marla' : '10_marla') as PlotPreset,
              plotWidthFt: bp.plot_width || 35,
              plotLengthFt: bp.plot_length || 65,
              unit: 'feet' as PlotUnit,
              plotAreaSqFt: (bp.plot_width || 35) * (bp.plot_length || 65),
              plotAreaMarla: Math.round(((bp.plot_width || 35) * (bp.plot_length || 65)) / 225),
              floors: bp.floors || 2,
              bedrooms: bp.bedrooms || 4,
              bathrooms: bp.bathrooms || 5,
              style: (bp.style || 'Modern Contemporary') as ArchitecturalStyle,
              budgetMinPKR: 15000000,
              budgetMaxPKR: 25000000,
              status: bp.status || 'completed',
              creationMethod: 'prompt' as const,
              pakistaniSpecs: {
                groundFloorBedrooms: 2,
                firstFloorBedrooms: 2,
                drawingRoomSeparate: true,
                powderRoomNearEntrance: true,
                carPorchCapacity: 2,
                kitchenDirtyKitchenCombo: true,
                prayerArea: true,
                servantQuarter: true,
                laundryRoom: true,
                mumtyRooftopAccess: true,
                courtyardVentilation: true,
                setbackFrontFt: 7.5,
                setbackRearFt: 5,
                setbackSidesFt: 0,
              },
              designAlternatives: [],
              createdAt: bp.created_at ? bp.created_at.split('T')[0] : '2026-10-27',
              updatedAt: bp.updated_at ? bp.updated_at.split('T')[0] : '2026-10-27',
            }));
            const newOnes = formatted.filter((p: any) => !existingIds.has(p.id));
            return [...newOnes, ...prev];
          });
        }
      })
      .catch((err) => console.warn('Backend DB sync note:', err));
  }, []);

  const [templates, setTemplates] = useState<DesignTemplate[]>(MOCK_TEMPLATES);
  const [materialRates, setMaterialRates] = useState<MaterialRateItem[]>(MOCK_MATERIAL_RATES);
  const [costEstimates, setCostEstimates] = useState<CostEstimate[]>(INITIAL_COST_ESTIMATES);
  const [notifications, setNotifications] = useState<AppNotification[]>(INITIAL_NOTIFICATIONS);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(INITIAL_AUDIT_LOGS);

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationPhase, setGenerationPhase] = useState('');
  const [generationProgress, setGenerationProgress] = useState(0);

  useEffect(() => {
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  }, [projects]);

  const getProjectById = (id: string) => {
    return projects.find((p) => p.id === id);
  };

  const createProject = (data: Omit<Project, 'id' | 'createdAt' | 'updatedAt' | 'designAlternatives'>): Project => {
    const newId = `proj_${Date.now()}`;
    const now = new Date().toISOString().split('T')[0];

    const project: Project = {
      ...data,
      id: newId,
      designAlternatives: [],
      createdAt: now,
      updatedAt: now,
      status: 'draft',
    };

    setProjects((prev) => [project, ...prev]);

    // Save to backend database (saved_projects.json)
    syncProjectToSupabase(project).catch(console.warn);
    apiService.saveProject({
      id: newId,
      project_id: newId,
      name: project.title,
      title: project.title,
      plot_width: project.plotWidthFt,
      plot_length: project.plotLengthFt,
      floors: project.floors,
      bedrooms: project.bedrooms,
      bathrooms: project.bathrooms,
      style: project.style,
      status: project.status,
      created_at: new Date().toISOString()
    }).catch((err) => console.warn('Could not save to backend DB:', err));

    // Add audit log
    const log: AuditLog = {
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleString(),
      userName: data.ownerName || 'User',
      userRole: 'customer',
      action: 'PROJECT_CREATED',
      target: project.title,
      ipAddress: '127.0.0.1 (Local)',
      status: 'success',
    };
    setAuditLogs((prev) => [log, ...prev]);

    return project;
  };

  const updateProject = (id: string, updates: Partial<Project>) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, ...updates, updatedAt: new Date().toISOString().split('T')[0] } : p))
    );
  };

  const deleteProject = (id: string) => {
    setProjects((prev) => prev.filter((p) => p.id !== id));
  };

  const duplicateProject = (id: string): Project => {
    const original = projects.find((p) => p.id === id);
    if (!original) throw new Error('Project not found');

    const duplicated: Project = {
      ...original,
      id: `proj_${Date.now()}`,
      title: `${original.title} (Copy)`,
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0],
      status: 'draft',
      designAlternatives: original.designAlternatives.map((alt) => ({
        ...alt,
        id: `alt_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        projectId: `proj_${Date.now()}`,
      })),
    };

    setProjects((prev) => [duplicated, ...prev]);
    return duplicated;
  };

  const toggleFavoriteProject = (id: string) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, isFavorite: !p.isFavorite } : p))
    );
  };

  const toggleFavoriteTemplate = (id: string) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === id ? { ...t, isFavorite: !t.isFavorite } : t))
    );
  };

  const generateDesignAlternative = async (projectIdOrProject: string | Project, userNotes?: string): Promise<DesignAlternative> => {
    let project: Project | undefined;
    if (typeof projectIdOrProject === 'object' && projectIdOrProject !== null) {
      project = projectIdOrProject;
    } else {
      project = projects.find((p) => p.id === projectIdOrProject);
    }
    if (!project) {
      try {
        const saved = localStorage.getItem(PROJECTS_STORAGE_KEY);
        if (saved) {
          const parsed: Project[] = JSON.parse(saved);
          project = parsed.find((p) => p.id === projectIdOrProject);
        }
      } catch {}
    }
    if (!project) {
      project = INITIAL_PROJECTS[0];
    }

    setIsGenerating(true);
    setGenerationProgress(10);
    setGenerationPhase('Analyzing plot geometry, orientation & local bylaws (CDA/DHA/LDA)...');

    await new Promise((r) => setTimeout(r, 700));
    setGenerationProgress(35);
    setGenerationPhase('Optimizing spatial circulation, purdah zoning & cross-ventilation shafts...');

    await new Promise((r) => setTimeout(r, 800));
    setGenerationProgress(65);
    setGenerationPhase('Synthesizing 2D architectural CAD floor plan layout & structural spans...');

    await new Promise((r) => setTimeout(r, 700));
    setGenerationProgress(90);
    setGenerationPhase('Calculating preliminary construction Bill of Quantities (BOQ)...');

    await new Promise((r) => setTimeout(r, 600));
    setGenerationProgress(100);

    // Build realistic rooms based on plot size and specs
    const isFiveMarla = project.plotPreset === '5_marla' || project.plotAreaSqFt <= 1300;
    const isOneKanal = project.plotPreset === '1_kanal' || project.plotAreaSqFt >= 4000;

    const sampleRooms: RoomSpec[] = isFiveMarla
      ? [
          { id: 'r_p1', name: 'Car Porch (Sedan)', floor: 'Ground', widthFt: 14, lengthFt: 14, areaSqFt: 196, attachedBath: false },
          { id: 'r_d1', name: 'Front Drawing Room', floor: 'Ground', widthFt: 11, lengthFt: 14, areaSqFt: 154, attachedBath: true },
          { id: 'r_l1', name: 'Living & Dining Lounge', floor: 'Ground', widthFt: 14, lengthFt: 16, areaSqFt: 224, attachedBath: false },
          { id: 'r_k1', name: 'Kitchen with Airwell', floor: 'Ground', widthFt: 9, lengthFt: 11, areaSqFt: 99, attachedBath: false },
          { id: 'r_b1', name: 'Master Bed (Ground)', floor: 'Ground', widthFt: 12, lengthFt: 14, areaSqFt: 168, attachedBath: true },
          { id: 'r_b2', name: 'Bed 2 (First Floor)', floor: 'First', widthFt: 12, lengthFt: 14, areaSqFt: 168, attachedBath: true },
          { id: 'r_b3', name: 'Bed 3 (First Floor)', floor: 'First', widthFt: 11, lengthFt: 13, areaSqFt: 143, attachedBath: true, hasBalcony: true },
        ]
      : isOneKanal
      ? [
          { id: 'r_p1', name: 'Grand 3-Car Covered Porch', floor: 'Ground', widthFt: 24, lengthFt: 20, areaSqFt: 480, attachedBath: false },
          { id: 'r_d1', name: 'Formal Drawing Room', floor: 'Ground', widthFt: 18, lengthFt: 22, areaSqFt: 396, attachedBath: true },
          { id: 'r_d2', name: 'Formal Dining Room', floor: 'Ground', widthFt: 14, lengthFt: 18, areaSqFt: 252, attachedBath: false },
          { id: 'r_l1', name: 'Double Height Family Lounge', floor: 'Ground', widthFt: 22, lengthFt: 26, areaSqFt: 572, attachedBath: false },
          { id: 'r_k1', name: 'Show Kitchen + Dirty Kitchen', floor: 'Ground', widthFt: 16, lengthFt: 18, areaSqFt: 288, attachedBath: false },
          { id: 'r_b1', name: 'Master Bedroom 1 with Dresser', floor: 'Ground', widthFt: 16, lengthFt: 20, areaSqFt: 320, attachedBath: true },
          { id: 'r_b2', name: 'Guest Bedroom (Ground)', floor: 'Ground', widthFt: 14, lengthFt: 16, areaSqFt: 224, attachedBath: true },
          { id: 'r_b3', name: 'Executive Master Suite 2', floor: 'First', widthFt: 18, lengthFt: 22, areaSqFt: 396, attachedBath: true, hasBalcony: true },
          { id: 'r_b4', name: 'Bedroom 4 (Upper)', floor: 'First', widthFt: 15, lengthFt: 16, areaSqFt: 240, attachedBath: true },
          { id: 'r_b5', name: 'Bedroom 5 (Upper)', floor: 'First', widthFt: 14, lengthFt: 16, areaSqFt: 224, attachedBath: true },
          { id: 'r_b6', name: 'Study / Home Cinema Room', floor: 'First', widthFt: 16, lengthFt: 18, areaSqFt: 288, attachedBath: false },
          { id: 'r_sq', name: 'Dual Servant Quarters with Bath', floor: 'Rooftop', widthFt: 12, lengthFt: 18, areaSqFt: 216, attachedBath: true },
        ]
      : [
          { id: 'r_p1', name: 'Car Porch (Double SUV)', floor: 'Ground', widthFt: 18, lengthFt: 16, areaSqFt: 288, attachedBath: false },
          { id: 'r_d1', name: 'Guest Drawing Room', floor: 'Ground', widthFt: 14, lengthFt: 18, areaSqFt: 252, attachedBath: true },
          { id: 'r_l1', name: 'Central Family Lounge', floor: 'Ground', widthFt: 18, lengthFt: 22, areaSqFt: 396, attachedBath: false },
          { id: 'r_k1', name: 'Main Kitchen + Dirty Kitchen', floor: 'Ground', widthFt: 12, lengthFt: 16, areaSqFt: 192, attachedBath: false },
          { id: 'r_b1', name: 'Master Bed (Ground)', floor: 'Ground', widthFt: 14, lengthFt: 16, areaSqFt: 224, attachedBath: true },
          { id: 'r_b2', name: 'Bed 2 (Ground)', floor: 'Ground', widthFt: 13, lengthFt: 14, areaSqFt: 182, attachedBath: true },
          { id: 'r_b3', name: 'Upper Master Bed (First)', floor: 'First', widthFt: 14, lengthFt: 17, areaSqFt: 238, attachedBath: true, hasBalcony: true },
          { id: 'r_b4', name: 'Bed 4 (First)', floor: 'First', widthFt: 13, lengthFt: 15, areaSqFt: 195, attachedBath: true },
        ];

    const coveredArea = Math.round(project.plotAreaSqFt * (project.floors === 1 ? 0.75 : 1.55));
    const altCount = (project.designAlternatives?.length || 0) + 1;
    const letter = String.fromCharCode(64 + altCount); // A, B, C...

    const newAlternative: DesignAlternative = {
      id: `alt_${project.id}_${Date.now()}`,
      projectId: project.id,
      name: `AI Design Alternative ${letter} (${project.style})`,
      version: `v1.${altCount}`,
      summary: userNotes || `Intelligent layout generated for ${project.plotWidthFt}x${project.plotLengthFt} ft plot optimizing natural light and local setback requirements.`,
      floors: project.floors,
      coveredAreaSqFt: coveredArea,
      bedrooms: project.bedrooms,
      bathrooms: project.bathrooms,
      carParks: project.pakistaniSpecs.carPorchCapacity || 1,
      style: project.style,
      estimatedCostPKR: Math.round(coveredArea * 7600),
      floorPlanSvgType: isFiveMarla ? '5_marla_modern' : isOneKanal ? '1_kanal_estate' : '10_marla_luxury',
      naturalLightRating: Math.floor(86 + Math.random() * 10),
      privacyRating: Math.floor(88 + Math.random() * 10),
      spaceEfficiencyRating: Math.floor(89 + Math.random() * 8),
      warnings: [
        `Ensure front setback conforms to regional development authority bylaws (${project.pakistaniSpecs.setbackFrontFt} ft indicated).`,
        `Waterproofing and damp-proof course (DPC) recommended at plinth level.`,
      ],
      assumptions: [
        'Calculated based on grade-60 deformed rebar and standard load-bearing structural RCC framing.',
        'Illumination vectors calculated assuming East-facing primary front elevation.',
      ],
      createdAt: new Date().toISOString().split('T')[0],
      rooms: sampleRooms,
    };

    // Update project state
    setProjects((prev) =>
      prev.map((p) => {
        const targetId = typeof projectIdOrProject === 'object' ? projectIdOrProject.id : projectIdOrProject;
        if (p.id === targetId) {
          const updatedAlts = [...(p.designAlternatives || []), newAlternative];
          return {
            ...p,
            designAlternatives: updatedAlts,
            selectedAlternativeId: newAlternative.id,
            status: 'ready_for_review',
            updatedAt: new Date().toISOString().split('T')[0],
          };
        }
        return p;
      })
    );

    // Also automatically create an associated preliminary cost estimate
    const est = calculatePreliminaryCost({
      projectId: project.id,
      projectTitle: project.title,
      coveredAreaSqFt: coveredArea,
      floors: project.floors,
      category: 'premium',
      city: 'Islamabad/Rawalpindi',
    });
    setCostEstimates((prev) => [est, ...prev]);

    // Send notification
    const notif: AppNotification = {
      id: `notif_${Date.now()}`,
      userId: project.ownerId,
      title: 'New Design Generated',
      message: `Alternative ${letter} generated successfully with ${newAlternative.rooms.length} room specifications.`,
      type: 'generation',
      timestamp: 'Just now',
      read: false,
      link: `/app/designs/${project.id}`,
    };
    setNotifications((prev) => [notif, ...prev]);

    setIsGenerating(false);
    return newAlternative;
  };

  const addCostEstimate = (estimate: CostEstimate) => {
    setCostEstimates((prev) => [estimate, ...prev]);
  };

  const updateMaterialRate = (id: string, newRate: number) => {
    setMaterialRates((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, currentRatePKR: newRate, lastUpdated: new Date().toISOString().split('T')[0] } : m
      )
    );
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const resetDemoData = () => {
    localStorage.removeItem(PROJECTS_STORAGE_KEY);
    setProjects(INITIAL_PROJECTS);
    setTemplates(MOCK_TEMPLATES);
    setMaterialRates(MOCK_MATERIAL_RATES);
    setCostEstimates(INITIAL_COST_ESTIMATES);
    setNotifications(INITIAL_NOTIFICATIONS);
    setAuditLogs(INITIAL_AUDIT_LOGS);
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        templates,
        materialRates,
        costEstimates,
        notifications,
        auditLogs,
        isGenerating,
        generationPhase,
        generationProgress,
        getProjectById,
        createProject,
        updateProject,
        deleteProject,
        duplicateProject,
        toggleFavoriteProject,
        toggleFavoriteTemplate,
        generateDesignAlternative,
        addCostEstimate,
        updateMaterialRate,
        markNotificationRead,
        markAllNotificationsRead,
        resetDemoData,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProjects = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProjects must be used within a ProjectProvider');
  }
  return context;
};
