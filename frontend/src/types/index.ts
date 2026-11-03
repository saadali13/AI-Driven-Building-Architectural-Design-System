export type UserRole = 'customer' | 'architect' | 'admin' | 'contractor';

export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: UserRole;
  avatar?: string;
  firmName?: string;
  createdAt: string;
  status: 'active' | 'suspended' | 'pending';
}

export type PlotUnit = 'feet' | 'meters' | 'yards';
export type PlotPreset = '5_marla' | '7_marla' | '10_marla' | '1_kanal' | 'custom';

export type BuildingType = 'House' | 'Villa' | 'Apartment' | 'Commercial Building' | 'Other';
export type ArchitecturalStyle = 'Modern Contemporary' | 'Minimalist' | 'Traditional Pakistani' | 'Classical Neo-Colonial' | 'Brutalist' | 'Eco-Sustainable' | 'Spanish Villa' | 'Classical Estate' | 'Traditional Haveli';

export interface CustomRoomSpec {
  id: string;
  name: string;
  size: string; // e.g. '12x14 ft'
  floor?: 'Ground' | 'First';
}

export interface PakistaniSpecs {
  groundFloorBedrooms: number;
  firstFloorBedrooms: number;
  drawingRoomSeparate: boolean;
  powderRoomNearEntrance: boolean;
  carPorchCapacity: number; // 1, 2, 3, or 4 cars
  kitchenDirtyKitchenCombo: boolean; // Main show kitchen + dirty/mess kitchen
  prayerArea: boolean;
  servantQuarter: boolean;
  laundryRoom: boolean;
  mumtyRooftopAccess: boolean;
  courtyardVentilation: boolean;
  setbackFrontFt: number;
  setbackRearFt: number;
  setbackSidesFt: number;

  // Extended Pakistani Residential Features
  guardRoom?: boolean;

  // Formal Features
  formalDining?: boolean;
  doubleHeightFoyer?: boolean;

  // Foreign / Modern Features
  openKitchenIsland?: boolean;
  homeOffice?: boolean;
  walkInClosets?: boolean;
  pantryStore?: boolean;
  solarUtilityShaft?: boolean;

  // Custom Bedroom Sizing Preferences
  masterBedSize?: string;
  guestBedSize?: string;

  // Custom Rooms list
  customRooms?: CustomRoomSpec[];
}

export interface RoomSpec {
  id: string;
  name: string;
  floor: 'Ground' | 'First' | 'Second' | 'Rooftop';
  widthFt: number;
  lengthFt: number;
  areaSqFt: number;
  attachedBath: boolean;
  hasBalcony?: boolean;
  notes?: string;
}

export interface DesignAlternative {
  id: string;
  projectId: string;
  name: string;
  version: string;
  summary: string;
  floors: number;
  coveredAreaSqFt: number;
  bedrooms: number;
  bathrooms: number;
  carParks: number;
  style: ArchitecturalStyle;
  estimatedCostPKR: number;
  floorPlanSvgType: '5_marla_modern' | '10_marla_luxury' | '1_kanal_estate' | '7_marla_compact';
  rooms: RoomSpec[];
  naturalLightRating: number; // 1-100
  privacyRating: number;      // 1-100
  spaceEfficiencyRating: number; // 1-100
  warnings: string[];
  assumptions: string[];
  createdAt: string;
}

export interface Project {
  id: string;
  title: string;
  type: BuildingType;
  ownerId: string;
  ownerName: string;
  plotPreset: PlotPreset;
  plotWidthFt: number;
  plotLengthFt: number;
  unit: PlotUnit;
  plotAreaSqFt: number;
  plotAreaMarla: number;
  floors: number;
  bedrooms: number;
  bathrooms: number;
  style: ArchitecturalStyle;
  budgetMinPKR: number;
  budgetMaxPKR: number;
  status: 'draft' | 'generating' | 'ready_for_review' | 'completed' | 'archived' | 'failed';
  creationMethod: 'prompt' | 'form';
  promptText?: string;
  pakistaniSpecs: PakistaniSpecs;
  designAlternatives: DesignAlternative[];
  selectedAlternativeId?: string;
  assignedArchitectId?: string;
  assignedArchitectName?: string;
  createdAt: string;
  updatedAt: string;
  isFavorite?: boolean;
}

export interface MaterialRateItem {
  id: string;
  material: string;
  category: 'structural' | 'finishing' | 'services' | 'labour';
  unit: string;
  currentRatePKR: number;
  lastUpdated: string;
  benchmarkSource: string;
}

export interface CostBreakdown {
  greyStructure: number;
  foundationAndEarthwork: number;
  brickworkMasonry: number;
  cementSandCrush: number;
  steelRebar: number;
  plumbingSanitary: number;
  electricalWiringConduits: number;
  flooringTilesMarbles: number;
  doorsWindowsWoodMetal: number;
  paintFinishingFalseCeiling: number;
  kitchenBathFixtures: number;
  labourCost: number;
  contingencyAllowance: number;
}

export interface CostEstimate {
  id: string;
  projectId: string;
  projectTitle: string;
  designId?: string;
  coveredAreaSqFt: number;
  floors: number;
  category: 'economy' | 'standard' | 'premium' | 'luxury';
  regionalCity: 'Islamabad/Rawalpindi' | 'Lahore' | 'Karachi' | 'Peshawar' | 'Multan' | 'Faisalabad';
  currency: 'PKR' | 'USD';
  ratesDate: string;
  breakdown: CostBreakdown;
  totalEstimatedCostPKR: number;
  costPerSqFtPKR: number;
  scenarioMinPKR: number;
  scenarioTypicalPKR: number;
  scenarioMaxPKR: number;
  notes: string[];
  createdAt: string;
}

export interface DesignTemplate {
  id: string;
  name: string;
  category: string;
  plotCategory: PlotPreset;
  plotDimensions: string;
  areaSqFt: number;
  bedrooms: number;
  bathrooms: number;
  floors: number;
  style: ArchitecturalStyle;
  budgetPKR: number;
  description: string;
  features: string[];
  floorPlanSvgType: '5_marla_modern' | '10_marla_luxury' | '1_kanal_estate' | '7_marla_compact';
  isFavorite?: boolean;
  published: boolean;
}

export interface AppNotification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: 'generation' | 'review' | 'estimate' | 'system';
  timestamp: string;
  read: boolean;
  link?: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  userName: string;
  userRole: UserRole;
  action: string;
  target: string;
  ipAddress: string;
  status: 'success' | 'warning' | 'security_event';
}
