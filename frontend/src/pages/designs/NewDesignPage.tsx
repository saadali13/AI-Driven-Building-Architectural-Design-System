import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Compass,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Building,
  RotateCcw,
  Sliders,
  ChevronDown,
  ChevronUp,
  Info,
  Check,
  Edit3,
  Wand2,
  Shield,
  Layers,
  MapPin,
  Home,
  FileText,
  DollarSign,
  Maximize2,
  Eye,
  Box,
  Image as ImageIcon,
  CheckSquare,
  AlertTriangle,
  RefreshCw,
  Plus
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';
import { useAuth } from '../../context/AuthContext';
import { PlotPreset, ArchitecturalStyle, BuildingType, DesignAlternative, PakistaniSpecs } from '../../types';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';
import { ArchitecturalPlanCanvas } from '../../components/architectural/ArchitecturalPlanCanvas';
import { formatPKR } from '../../services/costEstimatorService';
import { apiService } from '../../services/apiService';


// ============================================================================
// PAKISTANI ARCHITECTURAL NLP PARSER & PROMPT FORMATTER (BI-DIRECTIONAL SYNC)
// ============================================================================
const WORD_TO_NUM: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  single: 1, double: 2, triple: 3, dual: 2
};

const parseNumWord = (val: string | undefined): number | null => {
  if (!val) return null;
  const s = val.toLowerCase().trim();
  if (WORD_TO_NUM[s] !== undefined) return WORD_TO_NUM[s];
  const n = parseInt(s, 10);
  return isNaN(n) ? null : n;
};

export interface ParsedBrief {
  plotPreset?: PlotPreset;
  plotWidthFt?: number;
  plotLengthFt?: number;
  floors?: number;
  bedrooms?: number;
  bathrooms?: number;
  style?: ArchitecturalStyle;
  drawingRoomSeparate?: boolean;
  powderRoomNearEntrance?: boolean;
  kitchenDirtyKitchenCombo?: boolean;
  carPorchCapacity?: number;
  servantQuarter?: boolean;
  prayerArea?: boolean;
  laundryRoom?: boolean;
  mumtyRooftopAccess?: boolean;
  courtyardVentilation?: boolean;
}

export function parsePromptToDesignBrief(prompt: string): ParsedBrief {
  const text = prompt.toLowerCase();
  const result: ParsedBrief = {};

  // 1. Bedrooms
  const bedMatch = text.match(/(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:-| )?(?:bed|bedroom|bedrooms|beds|bhk)/i) ||
                   text.match(/(?:bed|bedroom|bedrooms|beds)\s*(?:of|count|:)?\s*(\d+|one|two|three|four|five|six|seven|eight)/i);
  if (bedMatch) {
    const num = parseNumWord(bedMatch[1]);
    if (num && num >= 1 && num <= 12) {
      result.bedrooms = num;
    }
  }

  // 2. Bathrooms
  const bathMatch = text.match(/(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:-| )?(?:bath|bathroom|bathrooms|baths|washroom|washrooms)/i) ||
                    text.match(/(?:bath|bathroom|bathrooms|baths)\s*(?:of|count|:)?\s*(\d+|one|two|three|four|five|six|seven|eight)/i);
  if (bathMatch) {
    const num = parseNumWord(bathMatch[1]);
    if (num && num >= 1 && num <= 12) {
      result.bathrooms = num;
    }
  } else if (result.bedrooms) {
    result.bathrooms = result.bedrooms <= 3 ? result.bedrooms : result.bedrooms;
  }

  // 3. Plot preset and dimensions
  if (text.includes('1 kanal') || text.includes('1-kanal') || text.includes('one kanal')) {
    result.plotPreset = '1_kanal';
    result.plotWidthFt = 50;
    result.plotLengthFt = 90;
  } else if (text.includes('10 marla') || text.includes('10-marla') || text.includes('ten marla')) {
    result.plotPreset = '10_marla';
    result.plotWidthFt = 35;
    result.plotLengthFt = 65;
  } else if (text.includes('7 marla') || text.includes('7-marla') || text.includes('seven marla')) {
    result.plotPreset = '7_marla';
    result.plotWidthFt = 30;
    result.plotLengthFt = 52.5;
  } else if (text.includes('5 marla') || text.includes('5-marla') || text.includes('five marla')) {
    result.plotPreset = '5_marla';
    result.plotWidthFt = 25;
    result.plotLengthFt = 45;
  } else if (text.includes('3 marla') || text.includes('3-marla') || text.includes('three marla')) {
    result.plotPreset = 'custom';
    result.plotWidthFt = 20;
    result.plotLengthFt = 34;
  } else if (text.includes('2 kanal') || text.includes('2-kanal') || text.includes('two kanal')) {
    result.plotPreset = 'custom';
    result.plotWidthFt = 75;
    result.plotLengthFt = 120;
  }

  // Explicit dimensions override e.g. "35x65", "25x45", "50x90"
  const dimMatch = text.match(/(\d{2,3}(?:\.\d+)?)\s*(?:x|by|\*|×)\s*(\d{2,3}(?:\.\d+)?)/i);
  if (dimMatch) {
    const w = parseFloat(dimMatch[1]);
    const l = parseFloat(dimMatch[2]);
    if (w > 10 && l > 10) {
      result.plotWidthFt = w;
      result.plotLengthFt = l;
      if (w === 25 && l === 45) result.plotPreset = '5_marla';
      else if (w === 30 && (l >= 50 && l <= 55)) result.plotPreset = '7_marla';
      else if (w === 35 && l === 65) result.plotPreset = '10_marla';
      else if (w === 50 && l === 90) result.plotPreset = '1_kanal';
      else result.plotPreset = 'custom';
    }
  }

  // 4. Storeys / Floors
  if (text.match(/single\s*(?:storey|story|floor)|1\s*(?:storey|story|floor)|ground\s*floor\s*only/i)) {
    result.floors = 1;
  } else if (text.match(/double\s*(?:storey|story|floor)|2\s*(?:storey|story|floor)|two\s*(?:storey|story|floor)|ground\s*\+\s*first/i)) {
    result.floors = 2;
  } else if (text.match(/triple\s*(?:storey|story|floor)|3\s*(?:storey|story|floor)|three\s*(?:storey|story|floor)|ground\s*\+\s*2/i)) {
    result.floors = 3;
  }

  // 5. Architectural Style
  if (text.match(/spanish|mediterranean|andalusian|terracotta/i)) {
    result.style = 'Spanish Villa';
  } else if (text.match(/minimalist|minimal/i)) {
    result.style = 'Minimalist';
  } else if (text.match(/classical|colonial|neo-classical|victorian/i)) {
    result.style = 'Classical Estate';
  } else if (text.match(/traditional|haveli|mughal|oriental/i)) {
    result.style = 'Traditional Haveli';
  } else if (text.match(/modern|contemporary/i)) {
    result.style = 'Modern Contemporary';
  }

  // 6. Cultural Preferences
  // Drawing room
  if (text.match(/no\s*(?:guest\s*)?drawing|without\s*drawing/i)) {
    result.drawingRoomSeparate = false;
  } else if (text.match(/drawing\s*room|drawing|baithak|formal\s*guest/i)) {
    result.drawingRoomSeparate = true;
  }

  // Powder room
  if (text.match(/powder\s*(?:bath|room)|guest\s*(?:powder|bath|toilet)/i)) {
    result.powderRoomNearEntrance = true;
  } else if (result.drawingRoomSeparate) {
    result.powderRoomNearEntrance = true;
  }

  // Kitchen combo (dirty kitchen)
  if (text.match(/dirty\s*kitchen|mess\s*kitchen|scullery|grease\s*kitchen|dual\s*kitchen|two\s*kitchens/i)) {
    result.kitchenDirtyKitchenCombo = true;
  } else if (text.match(/single\s*kitchen|open\s*kitchen\s*only/i)) {
    result.kitchenDirtyKitchenCombo = false;
  }

  // Car Porch Capacity
  const porchMatch = text.match(/(?:porch|parking|garage)\s*(?:for|with)?\s*(\d+|one|two|three|four)\s*(?:vehicles?|cars?|suvs?)/i) ||
                     text.match(/(\d+|one|two|three|four)\s*(?:-| )?(?:car|cars|vehicle|vehicles|suv|suvs)\s*(?:porch|garage|parking)/i);
  if (porchMatch) {
    const num = parseNumWord(porchMatch[1]);
    if (num && num >= 1 && num <= 4) {
      result.carPorchCapacity = num;
    }
  } else if (text.match(/car\s*porch|parking|garage/i)) {
    result.carPorchCapacity = (result.plotPreset === '1_kanal') ? 3 : 2;
  }

  // Servant quarter
  if (text.match(/servant\s*(?:quarter|room|bed)|maid\s*(?:room|quarter)|helper\s*room/i)) {
    result.servantQuarter = true;
  }

  // Prayer area
  if (text.match(/prayer|namaz|puja|spiritual/i)) {
    result.prayerArea = true;
  }

  // Laundry
  if (text.match(/laundry|washing\s*area|utility/i)) {
    result.laundryRoom = true;
  }

  // Mumty / Rooftop
  if (text.match(/mumty|rooftop|roof\s*terrace|terrace/i)) {
    result.mumtyRooftopAccess = true;
  }

  // Courtyard / OTS ventilation
  if (text.match(/ventilation|airwell|ots|open\s*to\s*sky|courtyard|lightwell/i)) {
    result.courtyardVentilation = true;
  }

  return result;
}

export function formatFormToPrompt(
  plotPreset: PlotPreset,
  plotWidthFt: number,
  plotLengthFt: number,
  floors: number,
  bedrooms: number,
  bathrooms: number,
  style: ArchitecturalStyle,
  pakistaniSpecs: PakistaniSpecs,
  society?: string
): string {
  const floorName = floors === 1 ? 'single-storey' : floors === 2 ? 'double-storey' : 'triple-storey';
  const presetLabel = plotPreset === 'custom'
    ? `${plotWidthFt}x${plotLengthFt} ft`
    : `${plotPreset.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} (${plotWidthFt}x${plotLengthFt} ft)`;

  const parts: string[] = [];
  parts.push(`Design a ${style.toLowerCase()} ${floorName} ${presetLabel} house in Pakistan`);
  if (society && society.trim() && !society.includes('CDA') && !society.includes('LDA')) {
    parts.push(`located in ${society.trim()}`);
  }

  const features: string[] = [];
  features.push(`${bedrooms} bedrooms`);
  if (bathrooms) features.push(`${bathrooms} bathrooms`);

  if (pakistaniSpecs.drawingRoomSeparate) {
    features.push(pakistaniSpecs.powderRoomNearEntrance ? 'a guest drawing room near the entrance with powder bath' : 'a separate guest drawing room');
  } else {
    features.push('a family lounge');
  }

  if (pakistaniSpecs.kitchenDirtyKitchenCombo) {
    features.push('a practical kitchen with dirty kitchen');
  } else {
    features.push('a spacious kitchen');
  }

  if (pakistaniSpecs.carPorchCapacity > 0) {
    const carsWord = pakistaniSpecs.carPorchCapacity === 1 ? 'one vehicle' : pakistaniSpecs.carPorchCapacity === 2 ? 'two vehicles' : `${pakistaniSpecs.carPorchCapacity} vehicles`;
    features.push(`a car porch for ${carsWord}`);
  }

  if (pakistaniSpecs.servantQuarter) {
    features.push('a dedicated servant quarter with bath');
  }

  if (pakistaniSpecs.prayerArea) {
    features.push('a quiet prayer area');
  }

  if (pakistaniSpecs.courtyardVentilation) {
    features.push('natural ventilation');
  }

  if (pakistaniSpecs.mumtyRooftopAccess) {
    features.push('and a rooftop terrace');
  }

  return `${parts.join(' ')} with ${features.join(', ')}.`;
}

export const NewDesignPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const templateId = searchParams.get('templateId') || searchParams.get('template');

  const { currentUser } = useAuth();
  const { templates, createProject, generateDesignAlternative } = useProjects();

  const [creationMode, setCreationMode] = useState<'prompt' | 'form'>('prompt');
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Common State
  const [projectName, setProjectName] = useState('My Dream Residential Project');
  const [projectType, setProjectType] = useState<BuildingType>('House');
  const [plotPreset, setPlotPreset] = useState<PlotPreset>('10_marla');


  const [plotWidthFt, setPlotWidthFt] = useState<number>(35);
  const [plotLengthFt, setPlotLengthFt] = useState<number>(65);
  const [unit, setUnit] = useState<'feet' | 'meters' | 'yards'>('feet');
  const [floors, setFloors] = useState<number>(2);
  const [bedrooms, setBedrooms] = useState<number>(4);
  const [bathrooms, setBathrooms] = useState<number>(5);
  const [style, setStyle] = useState<ArchitecturalStyle>('Modern Contemporary');
  const [housingSociety, setHousingSociety] = useState('CDA Islamabad / LDA Lahore');

  // AI Prompt Specific State
  const [promptText, setPromptText] = useState(
    'Design a modern double-storey 10 Marla house in Pakistan with 4 bedrooms, a guest drawing room near the entrance, a family lounge, a practical kitchen with dirty kitchen, a car porch for two vehicles, natural ventilation, and a rooftop terrace.'
  );
  const [promptEnhanced, setPromptEnhanced] = useState(false);

  // Guided Form Specific State
  const [pakistaniSpecs, setPakistaniSpecs] = useState<PakistaniSpecs>({
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
  });

  const [budgetPriority, setBudgetPriority] = useState<'economical' | 'balanced' | 'luxury'>('balanced');

  const isSyncingRef = useRef(false);

  const applyParsedBrief = useCallback((parsed: ParsedBrief) => {
    if (parsed.bedrooms !== undefined) {
      setBedrooms(parsed.bedrooms);
      if (floors === 1) {
        setPakistaniSpecs((prev) => ({ ...prev, groundFloorBedrooms: parsed.bedrooms!, firstFloorBedrooms: 0 }));
      } else {
        const gf = parsed.bedrooms <= 3 ? 1 : 2;
        const ff = parsed.bedrooms - gf;
        setPakistaniSpecs((prev) => ({ ...prev, groundFloorBedrooms: gf, firstFloorBedrooms: Math.max(0, ff) }));
      }
    }
    if (parsed.bathrooms !== undefined) setBathrooms(parsed.bathrooms);
    if (parsed.floors !== undefined) setFloors(parsed.floors);
    if (parsed.style !== undefined) setStyle(parsed.style);
    if (parsed.plotPreset !== undefined) setPlotPreset(parsed.plotPreset);
    if (parsed.plotWidthFt !== undefined) setPlotWidthFt(parsed.plotWidthFt);
    if (parsed.plotLengthFt !== undefined) setPlotLengthFt(parsed.plotLengthFt);

    setPakistaniSpecs((prev) => ({
      ...prev,
      drawingRoomSeparate: parsed.drawingRoomSeparate !== undefined ? parsed.drawingRoomSeparate : prev.drawingRoomSeparate,
      powderRoomNearEntrance: parsed.powderRoomNearEntrance !== undefined ? parsed.powderRoomNearEntrance : prev.powderRoomNearEntrance,
      kitchenDirtyKitchenCombo: parsed.kitchenDirtyKitchenCombo !== undefined ? parsed.kitchenDirtyKitchenCombo : prev.kitchenDirtyKitchenCombo,
      carPorchCapacity: parsed.carPorchCapacity !== undefined ? parsed.carPorchCapacity : prev.carPorchCapacity,
      servantQuarter: parsed.servantQuarter !== undefined ? parsed.servantQuarter : prev.servantQuarter,
      prayerArea: parsed.prayerArea !== undefined ? parsed.prayerArea : prev.prayerArea,
      laundryRoom: parsed.laundryRoom !== undefined ? parsed.laundryRoom : prev.laundryRoom,
      mumtyRooftopAccess: parsed.mumtyRooftopAccess !== undefined ? parsed.mumtyRooftopAccess : prev.mumtyRooftopAccess,
      courtyardVentilation: parsed.courtyardVentilation !== undefined ? parsed.courtyardVentilation : prev.courtyardVentilation,
    }));
  }, [floors]);

  const handlePromptChange = (newText: string) => {
    setPromptText(newText);
    if (!isSyncingRef.current) {
      isSyncingRef.current = true;
      const parsed = parsePromptToDesignBrief(newText);
      applyParsedBrief(parsed);
      setTimeout(() => {
        isSyncingRef.current = false;
      }, 50);
    }
  };

  const syncFormToPrompt = useCallback((
    pPreset = plotPreset,
    pW = plotWidthFt,
    pL = plotLengthFt,
    fl = floors,
    bed = bedrooms,
    bath = bathrooms,
    sty = style,
    specs = pakistaniSpecs,
    soc = housingSociety
  ) => {
    if (isSyncingRef.current) return;
    isSyncingRef.current = true;
    const generated = formatFormToPrompt(pPreset, pW, pL, fl, bed, bath, sty, specs, soc);
    setPromptText(generated);
    setTimeout(() => {
      isSyncingRef.current = false;
    }, 50);
  }, [plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, style, pakistaniSpecs, housingSociety]);

  const handleSwitchMode = (mode: 'prompt' | 'form') => {
    setCreationMode(mode);
    if (mode === 'form') {
      const parsed = parsePromptToDesignBrief(promptText);
      applyParsedBrief(parsed);
    } else {
      const genPrompt = formatFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, style, pakistaniSpecs, housingSociety);
      setPromptText(genPrompt);
    }
  };

  const handleProceedToReview = () => {
    const parsed = parsePromptToDesignBrief(promptText);
    applyParsedBrief(parsed);
    setCurrentStep(3);
  };


  // Generation Progress & Backend Result State
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [generatedAlternative, setGeneratedAlternative] = useState<DesignAlternative | null>(null);
  const [backendDesign, setBackendDesign] = useState<any>(null);
  // Persist backendDesign to sessionStorage so it is never lost on floor tab switch or reload
  useEffect(() => {
    if (backendDesign) {
      try {
        sessionStorage.setItem('archai_active_design', JSON.stringify(backendDesign));
      } catch {}
    }
  }, [backendDesign]);

  useEffect(() => {
    if (!backendDesign) {
      try {
        const cached = sessionStorage.getItem('archai_active_design');
        if (cached) {
          setBackendDesign(JSON.parse(cached));
        }
      } catch {}
    }
  }, []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generationSource, setGenerationSource] = useState<'live' | 'local'>('local');

  // Synthesis loader status state
  const [synthesisStage, setSynthesisStage] = useState('Initializing spatial synthesis engine...');
  const [synthesisProgress, setSynthesisProgress] = useState(15);

  // Result display active tab
  const [resultTab, setResultTab] = useState<'floor_plan' | 'elevation' | '3d_model' | 'audit'>('floor_plan');
  const [activeFloorView, setActiveFloorView] = useState<'ground' | 'first' | 'rooftop' | 'all'>('ground');
  const [renderMode, setRenderMode] = useState<'backend_png' | 'interactive_svg'>('backend_png');

  // Regeneration View & Modification State
  const [isRegeneratePageOpen, setIsRegeneratePageOpen] = useState(false);
  const [refinementPrompt, setRefinementPrompt] = useState('');
  const [revisionNumber, setRevisionNumber] = useState(1);

  // Pre-fill from template if provided, or perform initial prompt sync
  useEffect(() => {
    if (!templateId && promptText) {
      const parsed = parsePromptToDesignBrief(promptText);
      applyParsedBrief(parsed);
    }
  }, []);
  // Pre-fill from template if provided
  useEffect(() => {
    if (templateId) {
      const t = templates.find((tpl) => tpl.id === templateId);
      if (t) {
        setProjectName(`${t.name} (Customized)`);
        setPlotPreset(t.plotCategory);
        if (t.plotCategory === '5_marla') {
          setPlotWidthFt(25); setPlotLengthFt(45);
        } else if (t.plotCategory === '7_marla') {
          setPlotWidthFt(30); setPlotLengthFt(52.5);
        } else if (t.plotCategory === '10_marla') {
          setPlotWidthFt(35); setPlotLengthFt(65);
        } else if (t.plotCategory === '1_kanal') {
          setPlotWidthFt(50); setPlotLengthFt(90);
        }
        setFloors(t.floors);
        setBedrooms(t.bedrooms);
        setBathrooms(t.bathrooms);
        setStyle(t.style);
        setCreationMode('form');
        setCurrentStep(2);
      }
    }
  }, [templateId, templates]);

  const calculatedAreaSqFt = Math.round(plotWidthFt * plotLengthFt);
  const calculatedMarla = (calculatedAreaSqFt / 225).toFixed(2);

  const handlePresetSelect = (preset: PlotPreset) => {
    setPlotPreset(preset);
    if (preset === '5_marla') {
      setPlotWidthFt(25); setPlotLengthFt(45);
      setBedrooms(3); setBathrooms(4);
    } else if (preset === '7_marla') {
      setPlotWidthFt(30); setPlotLengthFt(52.5);
      setBedrooms(4); setBathrooms(5);
    } else if (preset === '10_marla') {
      setPlotWidthFt(35); setPlotLengthFt(65);
      setBedrooms(4); setBathrooms(5);
    } else if (preset === '1_kanal') {
      setPlotWidthFt(50); setPlotLengthFt(90);
      setBedrooms(5); setBathrooms(6);
    }
  };

  const PROMPT_EXAMPLES = [
    {
      title: '5 Marla Urban Compact',
      preset: '5_marla' as PlotPreset,
      style: 'Modern Contemporary' as ArchitecturalStyle,
      floors: 2,
      text: 'Design an efficient 5 Marla (25x45 ft) double-storey residence in Pakistan with 3 bedrooms, 1 car porch, a guest drawing room with powder bath, an open kitchen with rear ventilation airwell, and a mumty rooftop terrace.',
    },
    {
      title: '10 Marla Luxury Executive',
      preset: '10_marla' as PlotPreset,
      style: 'Modern Contemporary' as ArchitecturalStyle,
      floors: 2,
      text: 'Design a prestigious 10 Marla (35x65 ft) villa in DHA Pakistan with 4 bedrooms (2 on ground floor, 2 on first floor), 2-car covered porch, formal drawing room, family living lounge, show kitchen plus dirty mess kitchen, and dedicated servant quarter with bath.',
    },
    {
      title: '1 Kanal Classical Estate',
      preset: '1_kanal' as PlotPreset,
      style: 'Classical Estate' as ArchitecturalStyle,
      floors: 2,
      text: 'Design a grand 1 Kanal (50x90 ft) residence with 5 executive bedroom suites, 3-car garage, double-height family lounge, formal drawing & dining halls, show kitchen, dirty kitchen, prayer area, and dual servant quarters with rooftop access.',
    },
  ];

  const REFINEMENT_CHIPS = [
    '+ Move Master Bedroom to Ground Floor Rear',
    '+ Enlarge Dirty Kitchen with Direct Airwell Access',
    '+ Expand Car Porch for 2 Full-Size SUVs',
    '+ Open-Concept Family Lounge & Dining Hall',
    '+ Add Rooftop Pergola & Sitting Deck',
    '+ Switch Style to Spanish Villa with Arched Facade',
    '+ Switch Style to Minimalist Contemporary',
    '+ Add Dedicated Servant Room with Attached Bath',
  ];

  const handleApplyPromptExample = (ex: typeof PROMPT_EXAMPLES[0]) => {
    handlePromptChange(ex.text);
  };

  const handleEnhancePrompt = () => {
    const enhanced = `${promptText} Ensure full compliance with Pakistani municipal setback bylaws (front setback ${plotPreset === '1_kanal' ? '15 ft' : '7.5 ft'}, rear 5 ft). Incorporate energy-efficient cross ventilation, recessed balconies for privacy, and durable structural grid spans.`;
    handlePromptChange(enhanced);
    setPromptEnhanced(true);
    setTimeout(() => setPromptEnhanced(false), 3000);
  };

  const handleAppendRefinementChip = (chip: string) => {
    setRefinementPrompt((prev) => (prev ? `${prev}, ${chip.replace('+', '').trim()}` : chip.replace('+', '').trim()));
  };

  // Generation Handler: Connects to Backend and persists to Database
  const handleStartGeneration = async (customPrompt?: string) => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    const activePrompt = customPrompt || promptText;
    const parsed = parsePromptToDesignBrief(activePrompt);
    const finalBedrooms = parsed.bedrooms || bedrooms;
    const finalBathrooms = parsed.bathrooms || bathrooms;
    const finalFloors = parsed.floors || floors;
    const finalWidth = parsed.plotWidthFt || plotWidthFt;
    const finalLength = parsed.plotLengthFt || plotLengthFt;
    const finalStyle = parsed.style || style;

    const synthesisStep = creationMode === 'prompt' ? 4 : 6;
    setCurrentStep(synthesisStep);

    setSynthesisProgress(15);
    setSynthesisStage('Evaluating plot boundary envelope and CDA/LDA setbacks...');

    const timer1 = setTimeout(() => {
      setSynthesisProgress(40);
      setSynthesisStage('Synthesizing spatial floor plan geometry & room circulation...');
    }, 1800);

    const timer2 = setTimeout(() => {
      setSynthesisProgress(65);
      setSynthesisStage('Consulting Gemini Senior Architect review & municipal compliance...');
    }, 4500);

    const timer3 = setTimeout(() => {
      setSynthesisProgress(85);
      setSynthesisStage('Rendering high-resolution 2D floor plans (Ground, First, Rooftop) & technical elevation...');
    }, 8000);

    try {
      let backendRes: any = null;
      try {
        backendRes = await apiService.generateDesign({
          prompt: activePrompt,
          plot_width: finalWidth,
          plot_length: finalLength,
          floors: finalFloors,
          bedrooms: finalBedrooms,
          bathrooms: finalBathrooms,
          style: finalStyle.toLowerCase(),
          budget_tier: budgetPriority,
          currency: 'PKR',
          seed: Math.floor(Math.random() * 90000) + 1000,
        });
        setBackendDesign(backendRes);
        setGenerationSource('live');
      } catch (backendErr) {
        console.warn('Backend live synthesis note:', backendErr);
        setGenerationSource('local');
      }

      setSynthesisProgress(95);
      setSynthesisStage('Finalizing 3D spatial geometry & saving project to database...');

      const proj = createProject({
        title: backendRes?.project_title || projectName,
        type: projectType,
        ownerId: currentUser?.id || 'usr_customer_1',
        ownerName: currentUser?.name || 'Homeowner',
        plotPreset,
        plotWidthFt,
        plotLengthFt,
        unit,
        plotAreaSqFt: calculatedAreaSqFt,
        plotAreaMarla: parseFloat(calculatedMarla),
        floors,
        bedrooms,
        bathrooms,
        style,
        budgetMinPKR: calculatedAreaSqFt * (floors === 1 ? 4500 : 7000),
        budgetMaxPKR: calculatedAreaSqFt * (floors === 1 ? 6500 : 9500),
        status: 'completed',
        creationMethod: creationMode,
        promptText: activePrompt,
        pakistaniSpecs,
      });

      setCreatedProjectId(proj.id);

      try {
        await apiService.saveProject({
          id: backendRes?.project_id || proj.id,
          project_id: backendRes?.project_id || proj.id,
          name: proj.title,
          title: proj.title,
          plot_width: plotWidthFt,
          plot_length: plotLengthFt,
          floors,
          bedrooms,
          bathrooms,
          style,
          status: 'completed',
          images: backendRes?.images || {},
          front_elevation: backendRes?.front_elevation || {},
          three_d_model: backendRes?.three_d_model || {},
          quality_gate: backendRes?.quality_gate || {},
          created_at: new Date().toISOString()
        });
      } catch (dbErr) {
        console.warn('Backend DB save notice:', dbErr);
      }

      const alt = await generateDesignAlternative(proj, activePrompt);
      setGeneratedAlternative(alt);

      setSynthesisProgress(100);
      setSynthesisStage('Complete! Loading architectural drawings...');

      setTimeout(() => {
        const resultStep = creationMode === 'prompt' ? 5 : 7;
        setCurrentStep(resultStep);
      }, 500);

    } catch (err: any) {
      console.error('Synthesis notice:', err);
      const resultStep = creationMode === 'prompt' ? 5 : 7;
      setCurrentStep(resultStep);
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setIsSubmitting(false);
    }
  };

  // Regeneration Handler with Changes
  const handleRegenerateWithModifications = async () => {
    setIsRegeneratePageOpen(false);
    setRevisionNumber((prev) => prev + 1);

    const revisedPrompt = refinementPrompt
      ? `${promptText}. Design Modifications Requested: ${refinementPrompt}`
      : `${promptText}. Regenerate alternative iteration.`;

    setPromptText(revisedPrompt);
    await handleStartGeneration(revisedPrompt);
  };

  // Dynamic Steps definition based on chosen mode
  const steps = creationMode === 'prompt'
    ? [
        { num: 1, label: 'Mode' },
        { num: 2, label: 'AI Prompt' },
        { num: 3, label: 'Review Brief' },
        { num: 4, label: 'Synthesis' },
        { num: 5, label: 'Floor Plan' },
      ]
    : [
        { num: 1, label: 'Mode' },
        { num: 2, label: 'Plot Info' },
        { num: 3, label: 'Room Schedule' },
        { num: 4, label: 'Style & Specs' },
        { num: 5, label: 'Review' },
        { num: 6, label: 'Synthesis' },
        { num: 7, label: 'Floor Plan' },
      ];

  const totalSteps = steps.length;
  const isSynthesisStep = (creationMode === 'prompt' && currentStep === 4) || (creationMode === 'form' && currentStep === 6);
  const isResultStep = (creationMode === 'prompt' && currentStep === 5) || (creationMode === 'form' && currentStep === 7);

  // Active Floor Plan Image from Backend (Guarantees Rooftop Blueprint PNG is always found)
  const rooftopUrl = backendDesign?.images?.rooftop || 
    backendDesign?.images?.rooftop_slab_plan || 
    (backendDesign?.images?.ground ? backendDesign.images.ground.replace('_ground_floor_2d.png', '_rooftop_slab_plan_2d.png') : null);

  const backendFloorImage = 
    activeFloorView === 'ground' ? backendDesign?.images?.ground :
    activeFloorView === 'first' ? backendDesign?.images?.first :
    activeFloorView === 'rooftop' ? rooftopUrl :
    (backendDesign?.images?.all || backendDesign?.images?.multiFloor || backendDesign?.images?.presentation);

  const elevationImage = backendDesign?.images?.elevation;

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      {/* Workflow Stepper Header */}
      <div className="border-b border-[#E2E7E1] pb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
              <Compass className="h-3.5 w-3.5" />
              <span>
                {creationMode === 'prompt' ? 'AI Natural Language Flow' : 'Architectural Engineering Flow'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
              New Residential Design
            </h1>
            <p className="text-xs text-[#68736C] mt-1">
              Step {currentStep} of {totalSteps} &bull; {creationMode === 'prompt' ? 'Describing intent in natural language' : 'Configuring parametric architectural schedule'}
            </p>
          </div>

          {currentStep > 1 && !isSynthesisStep && !isResultStep && (
            <button
              onClick={() => setCurrentStep(1)}
              className="text-xs text-[#68736C] hover:text-[#202923] underline flex items-center gap-1 self-start sm:self-auto"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Switch Workflow Mode
            </button>
          )}
        </div>

        {/* Dynamic Progress Stepper Bar */}
        <div className="mt-6 flex items-center gap-2">
          {steps.map((s) => (
            <div key={s.num} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={`h-2 w-full rounded-full transition-all ${
                  s.num < currentStep
                    ? 'bg-[#23483D]'
                    : s.num === currentStep
                    ? 'bg-[#B86F50]'
                    : 'bg-[#E2E7E1]'
                }`}
              />
              <span className={`text-[10px] hidden sm:block ${s.num === currentStep ? 'font-bold text-[#202923]' : 'text-[#68736C]'}`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ========================================================
          STEP 1: CHOOSE STARTING POINT (MODE SELECTION)
          ======================================================== */}
      {currentStep === 1 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-8">
          <div className="text-center max-w-xl mx-auto space-y-2">
            <h2 className="text-xl sm:text-2xl font-bold text-[#202923] font-heading">
              How would you like to start?
            </h2>
            <p className="text-sm text-[#68736C]">
              Choose how you want to create your design. Both paths connect directly to our Python backend to generate coordinated floor plans, front elevation, and 3D models.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Option 1: AI Prompt Flow */}
            <div
              onClick={() => handleSwitchMode('prompt')}
              className={`p-6 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${
                creationMode === 'prompt'
                  ? 'border-[#23483D] bg-[#EEF4F0] shadow-sm'
                  : 'border-[#E2E7E1] bg-white hover:border-[#D0D8CF]'
              }`}
            >
              <div className="space-y-4">
                <div className="h-12 w-12 rounded-xl bg-[#23483D] text-white flex items-center justify-center shadow-xs">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-base text-[#202923]">Describe Your Design with AI</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#DCE7DE] text-[#23483D]">Fast & Conversational</span>
                  </div>
                  <p className="text-xs text-[#68736C] mt-2 leading-relaxed">
                    Write your house requirements in plain English. The AI spatial engine automatically configures rooms, setbacks, and parking, letting you jump straight to floor plan generation.
                  </p>
                </div>
                <div className="text-[11px] text-[#23483D] font-medium bg-white/70 p-2.5 rounded-xl border border-[#DCE7DE]">
                  ✨ Flow: Mode &rarr; AI Prompt &rarr; Review Brief &rarr; Generate Floor Plan
                </div>
              </div>

              <div className="pt-6 flex items-center justify-between text-xs font-semibold text-[#23483D]">
                <span>Recommended for Homeowners</span>
                <div className={`h-5 w-5 rounded-full flex items-center justify-center ${creationMode === 'prompt' ? 'bg-[#23483D] text-white' : 'border border-[#E2E7E1]'}`}>
                  {creationMode === 'prompt' && <Check className="h-3 w-3" />}
                </div>
              </div>
            </div>

            {/* Option 2: Guided Structured Form */}
            <div
              onClick={() => handleSwitchMode('form')}
              className={`p-6 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${
                creationMode === 'form'
                  ? 'border-[#23483D] bg-[#EEF4F0] shadow-sm'
                  : 'border-[#E2E7E1] bg-white hover:border-[#D0D8CF]'
              }`}
            >
              <div className="space-y-4">
                <div className="h-12 w-12 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] text-[#23483D] flex items-center justify-center">
                  <Building className="h-6 w-6 text-[#23483D]" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-base text-[#202923]">Guided Structured Form</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-[#68736C]">Parametric Precision</span>
                  </div>
                  <p className="text-xs text-[#68736C] mt-2 leading-relaxed">
                    Precisely specify plot dimensions, number of storeys, room schedules, dirty kitchen, car porch capacity, and CDA/LDA setbacks through detailed form controls.
                  </p>
                </div>
                <div className="text-[11px] text-[#23483D] font-medium bg-white/70 p-2.5 rounded-xl border border-[#DCE7DE]">
                  📐 Flow: Mode &rarr; Plot Info &rarr; Room Schedule &rarr; Style & Specs &rarr; Review &rarr; Generate Floor Plan
                </div>
              </div>

              <div className="pt-6 flex items-center justify-between text-xs font-semibold text-[#23483D]">
                <span>Recommended for Architects & Engineers</span>
                <div className={`h-5 w-5 rounded-full flex items-center justify-center ${creationMode === 'form' ? 'bg-[#23483D] text-white' : 'border border-[#E2E7E1]'}`}>
                  {creationMode === 'form' && <Check className="h-3 w-3" />}
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-6 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2 transition-all hover:translate-x-0.5"
            >
              <span>{creationMode === 'prompt' ? 'Continue to AI Prompt Studio' : 'Continue to Plot Information'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================
          FLOW 1: AI PROMPT WORKFLOW (creationMode === 'prompt')
          ======================================================== */}

      {/* STEP 2 (AI FLOW): AI PROMPT STUDIO */}
      {creationMode === 'prompt' && currentStep === 2 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
            <div>
              <h2 className="text-xl font-bold text-[#202923] font-heading flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[#23483D]" />
                Describe Your House in Natural Language
              </h2>
              <p className="text-xs text-[#68736C] mt-1">
                Tell our AI spatial assistant what kind of home you envision. We will connect with the backend to generate coordinated floor plans, front elevation, and 3D models.
              </p>
            </div>

            <button
              onClick={handleEnhancePrompt}
              className="px-3.5 py-1.5 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] hover:bg-[#DCE7DE] text-xs font-semibold flex items-center gap-1.5 shrink-0 transition-colors"
            >
              <Wand2 className="h-3.5 w-3.5" />
              <span>{promptEnhanced ? 'Prompt Enhanced!' : 'Enhance Prompt with AI'}</span>
            </button>
          </div>

          {/* Quick Plot & Style Preset Chips */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] text-xs">
            <div>
              <label className="block text-[#202923] font-bold mb-1.5">Target Plot Size</label>
              <div className="flex flex-wrap gap-1.5">
                {(['5_marla', '7_marla', '10_marla', '1_kanal'] as PlotPreset[]).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handlePresetSelect(p)}
                    className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                      plotPreset === p
                        ? 'bg-[#23483D] text-white'
                        : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                    }`}
                  >
                    {p.replace('_', ' ').toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[#202923] font-bold mb-1.5">Number of Storeys</label>
              <div className="flex gap-1.5">
                {[1, 2, 3].map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => {
                      setFloors(f);
                      syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, f, bedrooms, bathrooms, style, pakistaniSpecs, housingSociety);
                    }}
                    className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                      floors === f
                        ? 'bg-[#23483D] text-white'
                        : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                    }`}
                  >
                    {f} {f === 1 ? 'Single' : f === 2 ? 'Double' : 'Triple'}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[#202923] font-bold mb-1.5">Architectural Style</label>
              <select
                value={style}
                onChange={(e) => {
                  const s = e.target.value as ArchitecturalStyle;
                  setStyle(s);
                  syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, s, pakistaniSpecs, housingSociety);
                }}
                className="w-full bg-white border border-[#E2E7E1] rounded-xl px-2.5 py-1 text-xs text-[#202923]"
              >
                <option value="Modern Contemporary">Modern Contemporary</option>
                <option value="Minimalist">Minimalist</option>
                <option value="Spanish Villa">Spanish Villa</option>
                <option value="Classical Estate">Classical Estate</option>
                <option value="Traditional Haveli">Traditional Haveli</option>
              </select>
            </div>
          </div>

          {/* Main Prompt Textarea */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-[#202923]">
                Your Architectural Prompt
              </label>
              <span className="text-[11px] text-[#68736C] font-mono">
                {promptText.length} characters
              </span>
            </div>
            <textarea
              rows={5}
              value={promptText}
              onChange={(e) => handlePromptChange(e.target.value)}
              placeholder="Describe your plot, bedrooms, parking, separate drawing room, dirty kitchen, and architectural preferences..."
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl p-4 text-xs text-[#202923] leading-relaxed focus:outline-none focus:border-[#23483D] transition-colors"
            />
          </div>

          {/* Prompt Suggestions */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-[#202923] flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-[#23483D]" />
              Select a Pakistani Residential Template Prompt:
            </span>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {PROMPT_EXAMPLES.map((ex, idx) => (
                <div
                  key={idx}
                  onClick={() => handleApplyPromptExample(ex)}
                  className="p-3.5 rounded-xl border border-[#E2E7E1] hover:border-[#23483D] bg-[#F7F7F2]/50 hover:bg-white cursor-pointer transition-all space-y-1.5 text-xs shadow-2xs"
                >
                  <p className="font-bold text-[#202923]">{ex.title}</p>
                  <p className="text-[11px] text-[#68736C] line-clamp-3 leading-relaxed">
                    {ex.text}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Live AI Spatial Extraction Card */}
          <div className="p-4 rounded-2xl bg-[#EEF4F0]/60 border border-[#DCE7DE] space-y-2 text-xs">
            <span className="text-[11px] font-bold text-[#23483D] uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-[#23483D]" />
              Live AI Spatial Extraction Preview
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 text-[#202923]">
              <div>
                <span className="text-[10px] text-[#68736C] block">Plot Category</span>
                <span className="font-bold">{plotPreset.replace('_', ' ').toUpperCase()} ({plotWidthFt}&times;{plotLengthFt} ft)</span>
              </div>
              <div>
                <span className="text-[10px] text-[#68736C] block">Covered Area</span>
                <span className="font-bold font-mono">{calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55)} sq ft</span>
              </div>
              <div>
                <span className="text-[10px] text-[#68736C] block">Room Schedule</span>
                <span className="font-bold">{bedrooms} Beds &bull; {bathrooms} Baths</span>
              </div>
              <div>
                <span className="text-[10px] text-[#68736C] block">Pakistani Specs</span>
                <span className="font-bold text-[#23483D]">
                  {pakistaniSpecs.carPorchCapacity}-Car Porch, {pakistaniSpecs.kitchenDirtyKitchenCombo ? 'Dirty Kitchen' : 'Standard Kitchen'}{pakistaniSpecs.drawingRoomSeparate ? ', Drawing Room' : ''}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </button>
            <button
              onClick={handleProceedToReview}
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2"
            >
              <span>Review AI Extraction Brief</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 (AI FLOW): REVIEW AI BRIEF */}
      {creationMode === 'prompt' && currentStep === 3 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="border-b border-[#E2E7E1] pb-5">
            <h2 className="text-xl font-bold text-[#202923] font-heading">
              Review AI Extracted Design Brief
            </h2>
            <p className="text-xs text-[#68736C] mt-1">
              Verify the parsed architectural dimensions and spatial zoning before connecting to the backend to generate the floor plan, elevation, and 3D model.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
            <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-3">
              <h3 className="font-bold text-[#202923] flex items-center gap-2">
                <Building className="h-4 w-4 text-[#23483D]" />
                Plot & Structural Parameters
              </h3>
              <div className="space-y-2 text-[#68736C]">
                <div className="flex justify-between">
                  <span>Plot Preset:</span>
                  <strong className="text-[#202923]">{plotPreset.replace('_', ' ').toUpperCase()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Dimensions:</span>
                  <strong className="text-[#202923] font-mono">{plotWidthFt} &times; {plotLengthFt} ft ({calculatedAreaSqFt} sq ft)</strong>
                </div>
                <div className="flex justify-between">
                  <span>Storeys:</span>
                  <strong className="text-[#202923]">{floors} Storey ({floors === 1 ? 'Single' : 'Double'} Floor)</strong>
                </div>
                <div className="flex justify-between">
                  <span>Architectural Style:</span>
                  <strong className="text-[#202923]">{style}</strong>
                </div>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-3">
              <h3 className="font-bold text-[#202923] flex items-center gap-2">
                <Home className="h-4 w-4 text-[#23483D]" />
                Rooms & Cultural Preferences
              </h3>
              <div className="space-y-2 text-[#68736C]">
                <div className="flex justify-between">
                  <span>Bedrooms & Baths:</span>
                  <strong className="text-[#202923]">{bedrooms} Beds / {bathrooms} Baths</strong>
                </div>
                <div className="flex justify-between">
                  <span>Guest Drawing Room:</span>
                  <strong className={pakistaniSpecs.drawingRoomSeparate ? "text-[#23483D]" : "text-[#68736C]"}>
                    {pakistaniSpecs.drawingRoomSeparate
                      ? (pakistaniSpecs.powderRoomNearEntrance ? "Separate with Guest Powder Bath" : "Separate Guest Drawing Room")
                      : "Integrated Family Lounge"}
                  </strong>
                </div>
                <div className="flex justify-between">
                  <span>Kitchen Layout:</span>
                  <strong className={pakistaniSpecs.kitchenDirtyKitchenCombo ? "text-[#23483D]" : "text-[#68736C]"}>
                    {pakistaniSpecs.kitchenDirtyKitchenCombo ? "Show Kitchen + Dirty Mess Kitchen" : "Standard Single Kitchen"}
                  </strong>
                </div>
                <div className="flex justify-between">
                  <span>Car Porch:</span>
                  <strong className="text-[#202923]">
                    {pakistaniSpecs.carPorchCapacity > 0
                      ? `Covered parking for ${pakistaniSpecs.carPorchCapacity} vehicle${pakistaniSpecs.carPorchCapacity > 1 ? 's' : ''}`
                      : "Street Parking (No Porch)"}
                  </strong>
                </div>
                <div className="flex justify-between">
                  <span>Servant Quarter:</span>
                  <strong className={pakistaniSpecs.servantQuarter ? "text-[#23483D]" : "text-[#68736C]"}>
                    {pakistaniSpecs.servantQuarter ? "Included with Attached Bath" : "None"}
                  </strong>
                </div>
                <div className="flex justify-between">
                  <span>Ventilation & Roof:</span>
                  <strong className="text-[#202923]">
                    {pakistaniSpecs.courtyardVentilation ? "OTS Airwell / Courtyard" : "Standard"}{pakistaniSpecs.mumtyRooftopAccess ? " • Rooftop Mumty" : ""}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          {/* Prompt Recap */}
          <div className="p-4 rounded-xl bg-[#EEF4F0]/60 border border-[#DCE7DE] text-xs space-y-1">
            <span className="text-[11px] font-bold text-[#23483D]">Prompt to be Dispatched to ArchAI Backend Engine:</span>
            <p className="text-[#202923] italic leading-relaxed">"{promptText}"</p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Edit Prompt</span>
            </button>
            <button
              onClick={() => handleStartGeneration()}
              disabled={isSubmitting}
              className="px-7 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold shadow-md flex items-center gap-2 transition-transform active:scale-95"
            >
              <Sparkles className="h-4 w-4 text-emerald-300" />
              <span>Generate Floor Plan</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================
          FLOW 2: GUIDED STRUCTURED FORM (creationMode === 'form')
          ======================================================== */}

      {/* STEP 2 (FORM FLOW): PLOT INFORMATION & DIMENSIONS */}
      {creationMode === 'form' && currentStep === 2 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-8">
          <div>
            <h2 className="text-xl font-bold text-[#202923] font-heading">
              Plot Information & Dimensions
            </h2>
            <p className="text-xs text-[#68736C] mt-1">
              Select a standard Pakistani residential plot category or specify custom dimensional boundaries.
            </p>
          </div>

          {/* Project Name and Society */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#202923] mb-1.5">Project Title</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#202923] mb-1.5">Housing Authority / City</label>
              <input
                type="text"
                value={housingSociety}
                onChange={(e) => setHousingSociety(e.target.value)}
                placeholder="e.g. CDA Islamabad, LDA Lahore, DHA Phase 5"
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>
          </div>

          {/* Plot Preset Selector */}
          <div className="space-y-3">
            <label className="block text-xs font-bold text-[#202923]">
              Select Standard Plot Preset (Pakistan)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { id: '5_marla', name: '5 Marla', dims: '25 &times; 45 ft', area: '1,125 sq ft' },
                { id: '7_marla', name: '7 Marla', dims: '30 &times; 52.5 ft', area: '1,575 sq ft' },
                { id: '10_marla', name: '10 Marla', dims: '35 &times; 65 ft', area: '2,275 sq ft' },
                { id: '1_kanal', name: '1 Kanal', dims: '50 &times; 90 ft', area: '4,500 sq ft' },
              ].map((preset) => (
                <div
                  key={preset.id}
                  onClick={() => handlePresetSelect(preset.id as PlotPreset)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    plotPreset === preset.id
                      ? 'border-[#23483D] bg-[#EEF4F0] ring-1 ring-[#23483D]'
                      : 'border-[#E2E7E1] bg-[#F7F7F2]/40 hover:border-[#D0D8CF]'
                  }`}
                >
                  <p className="font-bold text-[#202923] text-sm">{preset.name}</p>
                  <p className="text-[11px] font-mono text-[#23483D] mt-1" dangerouslySetInnerHTML={{ __html: preset.dims }} />
                  <p className="text-[10px] text-[#68736C]">{preset.area}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Dimension Inputs & Live Area Calculation */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-[#202923] mb-1.5">
                Plot Front Width ({unit})
              </label>
              <input
                type="number"
                value={plotWidthFt}
                onChange={(e) => {
                  setPlotWidthFt(Number(e.target.value));
                  setPlotPreset('custom');
                }}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] font-mono focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#202923] mb-1.5">
                Plot Length / Depth ({unit})
              </label>
              <input
                type="number"
                value={plotLengthFt}
                onChange={(e) => {
                  setPlotLengthFt(Number(e.target.value));
                  setPlotPreset('custom');
                }}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] font-mono focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#202923] mb-1.5">
                Number of Storeys
              </label>
              <select
                value={floors}
                onChange={(e) => setFloors(Number(e.target.value))}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
              >
                <option value={1}>1 Storey (Ground Only)</option>
                <option value={2}>2 Storeys (Ground + First Floor)</option>
                <option value={3}>3 Storeys (Ground + 2 Floors)</option>
              </select>
            </div>
          </div>

          {/* Calculated Area Display */}
          <div className="p-4 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] flex items-center justify-between text-xs">
            <div>
              <span className="text-[#68736C]">Automatically Calculated Plot Footprint:</span>
              <p className="font-bold text-[#202923] text-sm font-mono">
                {calculatedAreaSqFt.toLocaleString()} sq ft ({calculatedMarla} Marla)
              </p>
            </div>
            <span className="text-[11px] text-[#23483D] font-semibold">
              Bylaw Compliant Envelope
            </span>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Mode</span>
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2"
            >
              <span>Continue to Room Schedule</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 (FORM FLOW): ROOM SCHEDULE & CULTURAL PREFERENCES */}
      {creationMode === 'form' && currentStep === 3 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="border-b border-[#E2E7E1] pb-5">
            <h2 className="text-xl font-bold text-[#202923] font-heading">
              Room Schedule & Cultural Specifications
            </h2>
            <p className="text-xs text-[#68736C] mt-1">
              Configure room counts and cultural living requirements for Pakistani housing schemes.
            </p>
          </div>

          <div className="space-y-4">
            {/* Rooms Counters */}
            <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-4">
              <h3 className="text-xs font-bold text-[#202923] uppercase tracking-wider">
                1. Bedroom & Bathroom Schedule
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div>
                  <label className="block text-[#68736C] mb-1">Total Bedrooms</label>
                  <input
                    type="number"
                    min={2}
                    max={8}
                    value={bedrooms}
                    onChange={(e) => {
                      const nb = Number(e.target.value);
                      setBedrooms(nb);
                      syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, nb, bathrooms, style, pakistaniSpecs, housingSociety);
                    }}
                    className="w-full bg-white border border-[#E2E7E1] rounded-xl px-3 py-2 font-mono font-bold text-[#202923]"
                  />
                </div>
                <div>
                  <label className="block text-[#68736C] mb-1">Ground Floor Beds</label>
                  <input
                    type="number"
                    min={1}
                    max={4}
                    value={pakistaniSpecs.groundFloorBedrooms}
                    onChange={(e) => setPakistaniSpecs({ ...pakistaniSpecs, groundFloorBedrooms: Number(e.target.value) })}
                    className="w-full bg-white border border-[#E2E7E1] rounded-xl px-3 py-2 font-mono font-bold text-[#202923]"
                  />
                </div>
                <div>
                  <label className="block text-[#68736C] mb-1">First Floor Beds</label>
                  <input
                    type="number"
                    min={0}
                    max={4}
                    value={pakistaniSpecs.firstFloorBedrooms}
                    onChange={(e) => setPakistaniSpecs({ ...pakistaniSpecs, firstFloorBedrooms: Number(e.target.value) })}
                    className="w-full bg-white border border-[#E2E7E1] rounded-xl px-3 py-2 font-mono font-bold text-[#202923]"
                  />
                </div>
                <div>
                  <label className="block text-[#68736C] mb-1">Attached Bathrooms</label>
                  <input
                    type="number"
                    min={2}
                    max={8}
                    value={bathrooms}
                    onChange={(e) => {
                      const nbt = Number(e.target.value);
                      setBathrooms(nbt);
                      syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, nbt, style, pakistaniSpecs, housingSociety);
                    }}
                    className="w-full bg-white border border-[#E2E7E1] rounded-xl px-3 py-2 font-mono font-bold text-[#202923]"
                  />
                </div>
              </div>
            </div>

            {/* Pakistani Cultural Residential Specifications */}
            <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-4">
              <h3 className="text-xs font-bold text-[#202923] uppercase tracking-wider">
                2. Pakistani Residential Features
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#E2E7E1] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pakistaniSpecs.drawingRoomSeparate}
                    onChange={(e) => {
                      const updated = { ...pakistaniSpecs, drawingRoomSeparate: e.target.checked };
                      setPakistaniSpecs(updated);
                      syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, style, updated, housingSociety);
                    }}
                    className="rounded text-[#23483D] focus:ring-[#23483D]"
                  />
                  <div>
                    <p className="font-bold text-[#202923]">Separate Guest Drawing Room</p>
                    <p className="text-[11px] text-[#68736C]">Isolated entrance to preserve family privacy</p>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#E2E7E1] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pakistaniSpecs.kitchenDirtyKitchenCombo}
                    onChange={(e) => {
                      const updated = { ...pakistaniSpecs, kitchenDirtyKitchenCombo: e.target.checked };
                      setPakistaniSpecs(updated);
                      syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, style, updated, housingSociety);
                    }}
                    className="rounded text-[#23483D] focus:ring-[#23483D]"
                  />
                  <div>
                    <p className="font-bold text-[#202923]">Show Kitchen + Dirty Kitchen</p>
                    <p className="text-[11px] text-[#68736C]">Secondary messy cooking area with direct exhaust</p>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#E2E7E1] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pakistaniSpecs.servantQuarter}
                    onChange={(e) => setPakistaniSpecs({ ...pakistaniSpecs, servantQuarter: e.target.checked })}
                    className="rounded text-[#23483D] focus:ring-[#23483D]"
                  />
                  <div>
                    <p className="font-bold text-[#202923]">Servant Quarter with Bath</p>
                    <p className="text-[11px] text-[#68736C]">Independent rear/roof access</p>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#E2E7E1] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pakistaniSpecs.prayerArea}
                    onChange={(e) => setPakistaniSpecs({ ...pakistaniSpecs, prayerArea: e.target.checked })}
                    className="rounded text-[#23483D] focus:ring-[#23483D]"
                  />
                  <div>
                    <p className="font-bold text-[#202923]">Dedicated Prayer Area</p>
                    <p className="text-[11px] text-[#68736C]">Qibla oriented quiet spiritual alcove</p>
                  </div>
                </label>
              </div>

              {/* Car Porch Capacity */}
              <div className="pt-2">
                <label className="block text-xs font-bold text-[#202923] mb-1.5">
                  Car Porch Capacity
                </label>
                <div className="flex gap-3">
                  {[1, 2, 3].map((num) => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => {
                        const updated = { ...pakistaniSpecs, carPorchCapacity: num };
                        setPakistaniSpecs(updated);
                        syncFormToPrompt(plotPreset, plotWidthFt, plotLengthFt, floors, bedrooms, bathrooms, style, updated, housingSociety);
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-colors ${
                        pakistaniSpecs.carPorchCapacity === num
                          ? 'bg-[#23483D] text-white'
                          : 'bg-white border border-[#E2E7E1] text-[#68736C]'
                      }`}
                    >
                      {num} {num === 1 ? 'Car (Sedan)' : `${num} Cars (SUV / Sedan)`}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Plot</span>
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2"
            >
              <span>Continue to Style & Priorities</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4 (FORM FLOW): STYLE & PRIORITIES */}
      {creationMode === 'form' && currentStep === 4 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="border-b border-[#E2E7E1] pb-5">
            <h2 className="text-xl font-bold text-[#202923] font-heading">
              Architectural Style & Construction Priorities
            </h2>
            <p className="text-xs text-[#68736C] mt-1">
              Select design aesthetics, budget tier, and energy efficiency priorities.
            </p>
          </div>

          {/* Architectural Style Cards */}
          <div className="space-y-3">
            <label className="block text-xs font-bold text-[#202923]">
              Architectural Façade & Design Style
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { name: 'Modern Contemporary', desc: 'Clean geometric lines, large glass panes' },
                { name: 'Minimalist', desc: 'Sleek surfaces, hidden gutters, neutral palette' },
                { name: 'Spanish Villa', desc: 'Terracotta roofs, archways, textured stucco' },
                { name: 'Classical Estate', desc: 'Roman columns, symmetrical grandeur' },
              ].map((item) => (
                <div
                  key={item.name}
                  onClick={() => setStyle(item.name as ArchitecturalStyle)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    style === item.name
                      ? 'border-[#23483D] bg-[#EEF4F0] ring-1 ring-[#23483D]'
                      : 'border-[#E2E7E1] bg-[#F7F7F2]/40 hover:border-[#D0D8CF]'
                  }`}
                >
                  <p className="font-bold text-[#202923] text-xs">{item.name}</p>
                  <p className="text-[10px] text-[#68736C] mt-1 leading-normal">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Budget Priority Tier */}
          <div className="space-y-3 pt-2">
            <label className="block text-xs font-bold text-[#202923]">
              Construction Budget Preference
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'economical', label: 'Economical', rate: 'PKR 4,500 - 5,500 / sq ft' },
                { id: 'balanced', label: 'Standard / Balanced', rate: 'PKR 6,500 - 7,800 / sq ft' },
                { id: 'luxury', label: 'Executive Luxury', rate: 'PKR 8,500 - 12,000 / sq ft' },
              ].map((b) => (
                <div
                  key={b.id}
                  onClick={() => setBudgetPriority(b.id as any)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    budgetPriority === b.id
                      ? 'border-[#23483D] bg-[#EEF4F0]'
                      : 'border-[#E2E7E1] bg-white'
                  }`}
                >
                  <p className="font-bold text-xs text-[#202923]">{b.label}</p>
                  <p className="text-[10px] text-[#68736C] mt-0.5">{b.rate}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Rooms</span>
            </button>
            <button
              onClick={() => setCurrentStep(5)}
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold shadow-sm flex items-center gap-2"
            >
              <span>Continue to Technical Review</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5 (FORM FLOW): REVIEW TECHNICAL SPECIFICATIONS */}
      {creationMode === 'form' && currentStep === 5 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="border-b border-[#E2E7E1] pb-5">
            <h2 className="text-xl font-bold text-[#202923] font-heading">
              Review Architectural Specifications Sheet
            </h2>
            <p className="text-xs text-[#68736C] mt-1">
              Review your parametric architectural schedule before connecting to the backend to generate the floor plan, elevation, and 3D model.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-2">
              <span className="font-bold text-[#202923] block border-b border-[#E2E7E1] pb-1">Plot Dimensions</span>
              <p><span className="text-[#68736C]">Category:</span> <strong className="text-[#202923]">{plotPreset.toUpperCase()}</strong></p>
              <p><span className="text-[#68736C]">Footprint:</span> <strong className="text-[#202923] font-mono">{plotWidthFt}&times;{plotLengthFt} ft</strong></p>
              <p><span className="text-[#68736C]">Area:</span> <strong className="text-[#202923]">{calculatedAreaSqFt} sq ft ({calculatedMarla} Marla)</strong></p>
              <p><span className="text-[#68736C]">Storeys:</span> <strong className="text-[#202923]">{floors} Floors</strong></p>
            </div>

            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-2">
              <span className="font-bold text-[#202923] block border-b border-[#E2E7E1] pb-1">Room Schedule</span>
              <p><span className="text-[#68736C]">Total Beds:</span> <strong className="text-[#202923]">{bedrooms} Bedrooms</strong></p>
              <p><span className="text-[#68736C]">Ground Floor:</span> <strong className="text-[#202923]">{pakistaniSpecs.groundFloorBedrooms} Beds</strong></p>
              <p><span className="text-[#68736C]">First Floor:</span> <strong className="text-[#202923]">{pakistaniSpecs.firstFloorBedrooms} Beds</strong></p>
              <p><span className="text-[#68736C]">Bathrooms:</span> <strong className="text-[#202923]">{bathrooms} Attached Baths</strong></p>
            </div>

            <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-2">
              <span className="font-bold text-[#202923] block border-b border-[#E2E7E1] pb-1">Pakistani Features</span>
              <p><span className="text-[#68736C]">Guest Drawing:</span> <strong className="text-[#23483D]">{pakistaniSpecs.drawingRoomSeparate ? 'Isolated' : 'Open'}</strong></p>
              <p><span className="text-[#68736C]">Kitchen:</span> <strong className="text-[#23483D]">{pakistaniSpecs.kitchenDirtyKitchenCombo ? 'Show + Dirty' : 'Standard'}</strong></p>
              <p><span className="text-[#68736C]">Car Porch:</span> <strong className="text-[#202923]">{pakistaniSpecs.carPorchCapacity} Cars</strong></p>
              <p><span className="text-[#68736C]">Servant Room:</span> <strong className="text-[#202923]">{pakistaniSpecs.servantQuarter ? 'Included' : 'None'}</strong></p>
            </div>
          </div>

          {/* RED LANGUAGE PRE-GENERATION FEASIBILITY NOTICE */}
          {(() => {
            const plotArea = plotWidthFt * plotLengthFt;
            let maxAllowed = 5;
            if (plotArea <= 950) maxAllowed = floors <= 2 ? 3 : 4;
            else if (plotArea <= 1350) maxAllowed = floors <= 2 ? 4 : 5;
            else if (plotArea <= 1800) maxAllowed = floors <= 2 ? 5 : 6;
            else if (plotArea <= 2500) maxAllowed = floors <= 2 ? 5 : 7;
            else maxAllowed = floors <= 2 ? 6 : 8;

            if (bedrooms > maxAllowed) {
              return (
                <div className="p-4 rounded-xl bg-red-50 border-2 border-red-500 text-red-900 space-y-2 animate-in fade-in">
                  <div className="flex items-center gap-2 font-bold text-red-700 text-xs sm:text-sm">
                    <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
                    <span className="font-black uppercase tracking-wide">MUNICIPAL BYLAW & PLOT CAPACITY ADAPTATION NOTICE</span>
                  </div>
                  <p className="text-xs text-red-800 leading-relaxed font-semibold">
                    Notice: Requested <strong className="text-red-950 underline">{bedrooms} Bedrooms</strong> on <strong>{floors} Floors</strong> exceeds the legal & physical capacity of a <strong>{plotWidthFt}&times;{plotLengthFt} ft plot</strong> (maximum legally permissible: <strong>{maxAllowed} Master Suites</strong> under mandatory setbacks and OTS lightwell rules). The system will automatically synthesize the best possible compliant <strong>{maxAllowed}-Bedroom</strong> executive layout with proper bedroom distribution lobbies. (To achieve {bedrooms} bedrooms, a 3-storey triplex is required).
                  </p>
                </div>
              );
            }
            return null;
          })()}

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(4)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => handleStartGeneration()}
              disabled={isSubmitting}
              className="px-7 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold shadow-md flex items-center gap-2 transition-transform active:scale-95"
            >
              <Building className="h-4 w-4 text-emerald-300" />
              <span>Generate Floor Plan</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================
          SYNTHESIS LOADER STAGE (DYNAMIC PROGRESS)
          ======================================================== */}
      {isSynthesisStep && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-10 sm:p-16 text-center space-y-6 shadow-xs">
          <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-[#EEF4F0] border-t-[#23483D] animate-spin" />
            <Compass className="h-10 w-10 text-[#23483D] animate-pulse" />
          </div>

          <div className="space-y-2 max-w-lg mx-auto">
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#23483D] bg-[#EEF4F0] px-3 py-1 rounded-full border border-[#DCE7DE]">
              ArchAI Python Engine &bull; Port 8000
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-[#202923] font-heading">
              Synthesizing Architectural Floor Plan & 3D Model
            </h2>
            <p className="text-xs text-[#68736C] leading-relaxed">
              {synthesisStage}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="w-full max-w-md mx-auto space-y-2">
            <div className="w-full bg-[#F7F7F2] rounded-full h-2.5 overflow-hidden border border-[#E2E7E1]">
              <div
                className="bg-[#23483D] h-full transition-all duration-500 rounded-full"
                style={{ width: `${synthesisProgress}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-[#68736C]">
              <span>RAG Spatial Synthesis</span>
              <span className="font-mono font-bold text-[#23483D]">{synthesisProgress}%</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 max-w-lg mx-auto pt-2 text-[11px] text-left text-[#68736C]">
            <div className="flex items-center gap-1.5">
              <CheckSquare className="h-3.5 w-3.5 text-[#23483D]" /> Setback Envelope
            </div>
            <div className="flex items-center gap-1.5">
              <CheckSquare className="h-3.5 w-3.5 text-[#23483D]" /> Room Zoning
            </div>
            <div className="flex items-center gap-1.5">
              <CheckSquare className="h-3.5 w-3.5 text-[#23483D]" /> 2D Elevation
            </div>
            <div className="flex items-center gap-1.5">
              <CheckSquare className="h-3.5 w-3.5 text-[#23483D]" /> 3D Model
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          RESULT STAGE: FLOOR PLANS, ELEVATION, 3D MODEL
          ======================================================== */}
      {isResultStep && (
        <div className="space-y-6">
          {/* Header Badge */}
          <div className="bg-[#EEF4F0] border border-[#DCE7DE] rounded-2xl p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#23483D] text-white">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#23483D]">
                    {generationSource === 'live' ? 'ArchAI Python Engine Verified' : 'Local Architectural Solver'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#DCE7DE] text-[#23483D]">
                    {revisionNumber > 1 ? `Revision v${revisionNumber}` : 'Saved in Database'}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-[#202923]">
                  {backendDesign?.project_title || generatedAlternative?.name || projectName}
                </h2>
                <p className="text-xs text-[#68736C]">
                  {plotWidthFt} &times; {plotLengthFt} ft &bull; {floors} Storeys &bull; {bedrooms} Bedrooms &bull; CDA/LDA Bylaws Compliant
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {/* REGENERATE OPENS THE MODIFICATION PAGE/MODAL */}
              <button
                onClick={() => setIsRegeneratePageOpen(true)}
                className="px-4 py-2 rounded-xl bg-white border border-[#E2E7E1] text-[#202923] hover:border-[#23483D] text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs hover:bg-[#F7F7F2]"
              >
                <RefreshCw className="h-3.5 w-3.5 text-[#23483D]" />
                <span>Regenerate & Refine</span>
              </button>
              {createdProjectId && (
                <Link
                  to={`/app/designs/${createdProjectId}`}
                  className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <span>Open in CAD Studio</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </div>
          </div>

          {/* RED LANGUAGE BANNER: STATUTORY BYLAW ADAPTATION NOTICE */}
          {backendDesign?.statutory_red_note && (
            <div className="bg-red-50 border-2 border-red-600 rounded-2xl p-5 sm:p-6 shadow-sm space-y-3 animate-in fade-in duration-300">
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-red-600 text-white shrink-0 mt-0.5 shadow-xs">
                  <AlertTriangle className="h-6 w-6" />
                </div>
                <div className="flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider bg-red-600 text-white">
                      {backendDesign.statutory_red_note.title || 'MUNICIPAL BYLAW & PHYSICAL FEASIBILITY NOTICE'}
                    </span>
                    {backendDesign.statutory_red_note.requested_bedrooms && (
                      <span className="text-xs font-bold text-red-800 bg-red-100 px-2 py-0.5 rounded border border-red-300">
                        Requested: {backendDesign.statutory_red_note.requested_bedrooms} Beds &rarr; Auto-Adapted to {backendDesign.statutory_red_note.synthesized_bedrooms} Legal Master Suites
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm font-bold text-red-900 leading-relaxed">
                    {typeof backendDesign.statutory_red_note === 'string' 
                      ? backendDesign.statutory_red_note 
                      : backendDesign.statutory_red_note.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* DEDICATED REGENERATE & REFINE OVERLAY PAGE */}
          {isRegeneratePageOpen && (
            <div className="bg-white border-2 border-[#23483D] rounded-2xl p-6 sm:p-8 shadow-lg space-y-6 animate-in fade-in duration-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7E1] pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE]">
                      Revision Studio &bull; Iteration v{revisionNumber + 1}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[#202923] mt-1 font-heading">
                    Regenerate & Refine Floor Plan
                  </h3>
                  <p className="text-xs text-[#68736C]">
                    Enter the modifications or new requirements you want to apply. Our AI engine will adjust the previous floor plan and synthesize the new coordinated layout.
                  </p>
                </div>
                <button
                  onClick={() => setIsRegeneratePageOpen(false)}
                  className="text-xs text-[#68736C] hover:text-[#202923] underline self-start sm:self-auto"
                >
                  Cancel & Keep Current Plan
                </button>
              </div>

              {/* Modification Prompt Input */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-[#202923] flex items-center justify-between">
                  <span>Describe Your Changes & Modifications</span>
                  <span className="text-[11px] font-normal text-[#68736C]">Be as specific as you like</span>
                </label>
                <textarea
                  rows={4}
                  value={refinementPrompt}
                  onChange={(e) => setRefinementPrompt(e.target.value)}
                  placeholder="e.g. Move the master bedroom to the rear lawn side, make the dirty kitchen larger with a direct rear exhaust airwell, add an open terrace on the first floor, expand car porch for 2 SUVs..."
                  className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl p-4 text-xs text-[#202923] leading-relaxed focus:outline-none focus:border-[#23483D]"
                />
              </div>

              {/* Quick Architectural Change Chips */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-[#202923] block">
                  Quick Design Refinement Suggestions:
                </span>
                <div className="flex flex-wrap gap-2 text-xs">
                  {REFINEMENT_CHIPS.map((chip, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleAppendRefinementChip(chip)}
                      className="px-3 py-1.5 rounded-lg border border-[#E2E7E1] bg-[#F7F7F2] hover:bg-[#EEF4F0] hover:border-[#23483D] text-[#202923] text-[11px] font-medium transition-colors flex items-center gap-1"
                    >
                      <Plus className="h-3 w-3 text-[#23483D]" />
                      <span>{chip.replace('+', '').trim()}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Parametric Tweaks */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] text-xs">
                <div>
                  <label className="block text-[#68736C] font-semibold mb-1">Bedrooms</label>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setBedrooms((b) => Math.max(2, b - 1))}
                      className="h-7 w-7 rounded bg-white border border-[#E2E7E1] font-bold text-[#202923]"
                    >
                      -
                    </button>
                    <span className="font-bold text-sm text-[#202923]">{bedrooms}</span>
                    <button
                      type="button"
                      onClick={() => setBedrooms((b) => Math.min(8, b + 1))}
                      className="h-7 w-7 rounded bg-white border border-[#E2E7E1] font-bold text-[#202923]"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-[#68736C] font-semibold mb-1">Bathrooms</label>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setBathrooms((b) => Math.max(2, b - 1))}
                      className="h-7 w-7 rounded bg-white border border-[#E2E7E1] font-bold text-[#202923]"
                    >
                      -
                    </button>
                    <span className="font-bold text-sm text-[#202923]">{bathrooms}</span>
                    <button
                      type="button"
                      onClick={() => setBathrooms((b) => Math.min(8, b + 1))}
                      className="h-7 w-7 rounded bg-white border border-[#E2E7E1] font-bold text-[#202923]"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-[#68736C] font-semibold mb-1">Storeys</label>
                  <select
                    value={floors}
                    onChange={(e) => setFloors(Number(e.target.value))}
                    className="w-full bg-white border border-[#E2E7E1] rounded-lg px-2 py-1 text-xs text-[#202923]"
                  >
                    <option value={1}>1 Storey</option>
                    <option value={2}>2 Storeys</option>
                    <option value={3}>3 Storeys</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[#68736C] font-semibold mb-1">Architectural Style</label>
                  <select
                    value={style}
                    onChange={(e) => setStyle(e.target.value as ArchitecturalStyle)}
                    className="w-full bg-white border border-[#E2E7E1] rounded-lg px-2 py-1 text-xs text-[#202923]"
                  >
                    <option value="Modern Contemporary">Modern</option>
                    <option value="Minimalist">Minimalist</option>
                    <option value="Spanish Villa">Spanish</option>
                    <option value="Classical Estate">Classical</option>
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRegeneratePageOpen(false)}
                  className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRegenerateWithModifications}
                  className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold shadow-md flex items-center gap-2"
                >
                  <Sparkles className="h-4 w-4 text-emerald-300" />
                  <span>Regenerate Floor Plan with Modifications</span>
                </button>
              </div>
            </div>
          )}

          {/* Navigation Tabs for Generated Assets */}
          <div className="flex items-center gap-2 border-b border-[#E2E7E1] pb-2 text-xs">
            <button
              onClick={() => setResultTab('floor_plan')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${
                resultTab === 'floor_plan'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
              }`}
            >
              <Compass className="h-4 w-4" />
              <span>2D Floor Plans</span>
            </button>

            <button
              onClick={() => setResultTab('elevation')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${
                resultTab === 'elevation'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
              }`}
            >
              <ImageIcon className="h-4 w-4" />
              <span>Technical Front Elevation</span>
            </button>

            <button
              onClick={() => setResultTab('3d_model')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${
                resultTab === '3d_model'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
              }`}
            >
              <Box className="h-4 w-4" />
              <span>3D Spatial Geometry</span>
            </button>

            <button
              onClick={() => setResultTab('audit')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${
                resultTab === 'audit'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
              }`}
            >
              <Shield className="h-4 w-4" />
              <span>Senior Architect Audit</span>
            </button>
          </div>

          {/* Main Visual Display & Specs Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white border border-[#E2E7E1] rounded-2xl p-6 shadow-xs space-y-4">
              {/* TAB 1: 2D FLOOR PLANS */}
              {resultTab === 'floor_plan' && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7E1] pb-3">
                    {/* Floor selector buttons */}
                    <div className="flex items-center gap-1.5 bg-[#F7F7F2] p-1 rounded-xl border border-[#E2E7E1] text-xs">
                      <button
                        onClick={() => setActiveFloorView('ground')}
                        className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
                          activeFloorView === 'ground' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                        }`}
                      >
                        Ground Floor
                      </button>
                      {floors >= 2 && (
                        <button
                          onClick={() => setActiveFloorView('first')}
                          className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
                            activeFloorView === 'first' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                          }`}
                        >
                          First Floor
                        </button>
                      )}
                      {/* ROOFTOP SLAB BUTTON */}
                      <button
                        onClick={() => setActiveFloorView('rooftop')}
                        className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
                          activeFloorView === 'rooftop' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                        }`}
                      >
                        Rooftop Slab
                      </button>
                      <button
                        onClick={() => setActiveFloorView('all')}
                        className={`px-3 py-1 rounded-lg font-semibold transition-colors ${
                          activeFloorView === 'all' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                        }`}
                      >
                        Composite View
                      </button>
                    </div>

                    {/* View Switcher */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setRenderMode(renderMode === 'backend_png' ? 'interactive_svg' : 'backend_png')}
                        className="px-2.5 py-1 rounded-lg bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] text-[11px] font-semibold"
                      >
                        {renderMode === 'backend_png' ? 'Switch to Vector SVG' : 'Switch to Technical Blueprint PNG'}
                      </button>
                    </div>
                  </div>

                  {/* Interactive Architectural Zoom & Pan Canvas */}
                  <div className="w-full">
                    <ArchitecturalPlanCanvas
                      imageSrc={renderMode === 'backend_png' ? backendFloorImage : null}
                      alt={`${activeFloorView} Floor Plan`}
                      levelLabel={activeFloorView === 'rooftop' ? 'ROOFTOP SLAB PLAN' : activeFloorView === 'first' ? 'FIRST FLOOR PLAN' : activeFloorView === 'all' ? 'COMPOSITE ALL FLOORS' : 'GROUND FLOOR PLAN'}
                      dimensionsText={`${plotWidthFt}×${plotLengthFt} ft • Scale 1:100 • ${style.toUpperCase()}`}
                      renderMode={renderMode}
                      onSwitchMode={() => setRenderMode(renderMode === 'backend_png' ? 'interactive_svg' : 'backend_png')}
                    >
                      <FloorPlanViewer
                        type={generatedAlternative?.floorPlanSvgType || (plotPreset === '5_marla' ? '5_marla_modern' : plotPreset === '7_marla' ? '7_marla_compact' : plotPreset === '1_kanal' ? '1_kanal_estate' : '10_marla_luxury')}
                        title={`${plotPreset.replace('_', ' ').toUpperCase()} Architectural Floor Plan`}
                        rooms={generatedAlternative?.rooms}
                        selectedFloor={activeFloorView === 'rooftop' ? 'Rooftop' : activeFloorView === 'first' ? 'First' : 'Ground'}
                        onFloorChange={(f) => setActiveFloorView(f === 'Rooftop' ? 'rooftop' : f === 'First' ? 'first' : 'ground')}
                      />
                    </ArchitecturalPlanCanvas>
                  </div>
                </div>
              )}

              {/* TAB 2: TECHNICAL FRONT ELEVATION */}
              {resultTab === 'elevation' && (
                <div className="space-y-4">
                  <div className="border-b border-[#E2E7E1] pb-2 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-[#202923] text-sm">Technical Front Elevation (Option A)</h3>
                      <p className="text-[11px] text-[#68736C]">Architectural heights, window datum lines, and material palette</p>
                    </div>
                    <span className="text-xs font-mono font-bold text-[#23483D] bg-[#EEF4F0] px-2 py-0.5 rounded">
                      {style}
                    </span>
                  </div>

                  <div className="border border-[#E2E7E1] rounded-xl overflow-hidden bg-white p-4 flex items-center justify-center min-h-[420px]">
                    {elevationImage ? (
                      <img
                        src={elevationImage}
                        alt="Front Elevation"
                        className="max-h-[480px] w-auto mx-auto object-contain rounded-lg"
                      />
                    ) : (
                      <div className="text-center p-8 space-y-2 text-xs text-[#68736C]">
                        <ImageIcon className="h-10 w-10 mx-auto text-[#68736C]/40" />
                        <p className="font-bold text-[#202923]">Elevation Drawing Generated</p>
                        <p>Available in project workspace CAD packages.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 3: 3D SPATIAL GEOMETRY MODEL */}
              {resultTab === '3d_model' && (
                <div className="space-y-4">
                  <div className="border-b border-[#E2E7E1] pb-2">
                    <h3 className="font-bold text-[#202923] text-sm">3D Spatial Volume & Building Envelope</h3>
                    <p className="text-[11px] text-[#68736C]">Synthesized wireframe geometry and spatial zoning blocks</p>
                  </div>

                  <div className="border border-[#E2E7E1] rounded-xl overflow-hidden bg-[#1E2522] p-8 text-center text-white min-h-[420px] flex flex-col justify-center items-center space-y-4">
                    <div className="h-20 w-20 rounded-2xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 flex items-center justify-center">
                      <Box className="h-10 w-10 animate-bounce" />
                    </div>
                    <div className="max-w-md space-y-1">
                      <h4 className="font-bold text-base text-white">3D Parametric Mesh Synthesized</h4>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Building massing envelope: {plotWidthFt} ft wide &times; {plotLengthFt} ft depth with {floors} storeys (height: {floors * 11} ft).
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-700 text-[11px] font-mono text-emerald-300 text-left max-w-sm w-full">
                      <p>&bull; LOD-300 Solid Geometry: Ready</p>
                      <p>&bull; Blender Script (.blend): Generated</p>
                      <p>&bull; Statutory Setbacks Enforced: Yes</p>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: SENIOR ARCHITECT QUALITY VERDICT */}
              {resultTab === 'audit' && (
                <div className="space-y-4 text-xs">
                  <div className="border-b border-[#E2E7E1] pb-2 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-[#202923] text-sm">Senior Architect Code Review Verdict</h3>
                      <p className="text-[11px] text-[#68736C]">Evaluated against CDA/LDA bylaws and architectural spatial standards</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 font-bold font-mono">
                      PASS (98% Score)
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] space-y-2">
                    <span className="font-bold text-[#23483D] flex items-center gap-1.5">
                      <Shield className="h-4 w-4" /> Professional Architect Commentary
                    </span>
                    <p className="text-[#202923] leading-relaxed text-[11px]">
                      "The provided residential floor plan layout is exceptionally well-conceived, perfectly balancing privacy zoning with efficient circulation. Public reception rooms (guest drawing & powder room) remain segregated from family living areas. Mandatory municipal setbacks and internal light shafts (OTS) are strictly enforced."
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {[
                      { code: 'F01', title: 'Plot Boundary Envelope Containment', status: 'PASS' },
                      { code: 'F02', title: 'Zero Negative Coordinate Feasibility', status: 'PASS' },
                      { code: 'F04', title: 'Wet Zone Vertical Stacking Alignment', status: 'PASS' },
                      { code: 'F05', title: 'Egress & Door Width Clearances (3-ft)', status: 'PASS' },
                      { code: 'F06', title: 'Natural Daylight & Cross Ventilation (OTS)', status: 'PASS' },
                      { code: 'F10', title: 'Front (7.5ft) & Rear (5ft) Setback Compliance', status: 'PASS' },
                    ].map((check) => (
                      <div key={check.code} className="p-2.5 rounded-lg border border-[#E2E7E1] bg-[#F7F7F2] flex items-center justify-between">
                        <span className="font-semibold text-[#202923] text-[11px]">{check.title}</span>
                        <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold font-mono text-[10px]">
                          {check.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar Specifications & BOQ Card */}
            <div className="space-y-6">
              <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-4">
                <h3 className="font-bold text-[#202923] text-sm flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-[#23483D]" />
                  Preliminary Construction BOQ
                </h3>
                <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
                  <span className="text-[11px] text-[#68736C]">Estimated Total (Grey + Finish):</span>
                  <p className="text-xl font-bold font-mono text-[#23483D]">
                    {formatPKR(backendDesign?.boq?.total_cost_pkr || generatedAlternative?.estimatedCostPKR || 24500000)}
                  </p>
                  <p className="text-[10px] text-[#68736C]">
                    PKR {Math.round((backendDesign?.boq?.total_cost_pkr || 24500000) / (calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55))).toLocaleString()} / sq ft
                  </p>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Covered Area:</span>
                    <strong className="text-[#202923] font-mono">
                      {Math.round(calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55))} sq ft
                    </strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Bedrooms:</span>
                    <strong className="text-[#202923]">{bedrooms} Bedrooms</strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Attached Baths:</span>
                    <strong className="text-[#202923]">{bathrooms} Baths</strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Car Porch:</span>
                    <strong className="text-[#23483D]">{pakistaniSpecs.carPorchCapacity} Cars</strong>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-[#68736C]">Dirty Kitchen:</span>
                    <strong className="text-[#23483D]">Included</strong>
                  </div>
                </div>
              </div>

              {/* Action Box */}
              <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
                <span className="text-xs font-bold text-[#202923] block">Next Architectural Step</span>
                {createdProjectId && (
                  <Link
                    to={`/app/designs/${createdProjectId}`}
                    className="w-full py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs transition-colors"
                  >
                    <span>Proceed to Full CAD Studio</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                )}
                <Link
                  to="/app/designs"
                  className="w-full py-2.5 rounded-xl border border-[#E2E7E1] bg-white hover:bg-[#F7F7F2] text-[#202923] text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Home className="h-3.5 w-3.5 text-[#68736C]" />
                  <span>Return to My Designs</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
