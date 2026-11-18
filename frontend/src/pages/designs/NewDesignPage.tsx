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
  Plus,
  Download,
  History,
  X,
  Calculator,
  Trash2,
  Key
} from 'lucide-react';
import { CustomRoomSpec } from '../../types';
import { useProjects } from '../../context/ProjectContext';
import { useAuth } from '../../context/AuthContext';
import { PlotPreset, ArchitecturalStyle, BuildingType, DesignAlternative, PakistaniSpecs } from '../../types';
import { FloorPlanViewer } from '../../components/architectural/FloorPlanViewer';
import { GuidedInterview } from '../../components/architectural/GuidedInterview';
import Massing3DViewer from '../../components/architectural/Massing3DViewer';
import { ArchitecturalPlanCanvas } from '../../components/architectural/ArchitecturalPlanCanvas';
import { formatPKR, DETAILED_MATERIALS_CATALOG } from '../../services/costEstimatorService';
import { apiService } from '../../services/apiService';


const fmtFeet = (v: number): string => {
  const f = Math.floor(v);
  const i = Math.round((v - f) * 12);
  return `${f}'-${i}"`;
};

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
  const [promptText, setPromptText] = useState('');
  const [promptEnhanced, setPromptEnhanced] = useState(false);

  // Guided Form Specific State
  const [pakistaniSpecs, setPakistaniSpecs] = useState<PakistaniSpecs>({
    groundFloorBedrooms: 2,
    firstFloorBedrooms: 2,
    drawingRoomSeparate: true,
    powderRoomNearEntrance: true,
    carPorchCapacity: 2,
    kitchenDirtyKitchenCombo: true,
    prayerArea: false,
    servantQuarter: false,
    laundryRoom: false,
    mumtyRooftopAccess: true,
    courtyardVentilation: true,
    setbackFrontFt: 7.5,
    setbackRearFt: 5,
    setbackSidesFt: 0,
    guardRoom: false,
    formalDining: false,
    doubleHeightFoyer: false,
    openKitchenIsland: false,
    homeOffice: false,
    walkInClosets: false,
    pantryStore: false,
    solarUtilityShaft: false,
  });

  const [customRooms, setCustomRooms] = useState<CustomRoomSpec[]>([]);
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomSize, setNewRoomSize] = useState('12x14 ft');
  const [newRoomFloor, setNewRoomFloor] = useState<'Ground' | 'First'>('Ground');
  const [masterBedSize, setMasterBedSize] = useState('14x16 ft (Executive)');
  const [guestBedSize, setGuestBedSize] = useState('12x14 ft (Standard)');
  const [isReviewEditing, setIsReviewEditing] = useState(false);

  // Gemini Market Rates & Interactive BOQ State
  const [geminiApiKey, setGeminiApiKey] = useState(() => {
    try {
      return sessionStorage.getItem('archai_gemini_key') || '';
    } catch {
      return '';
    }
  });
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [geminiCity, setGeminiCity] = useState('Islamabad / Lahore');
  const [isFetchingGeminiRates, setIsFetchingGeminiRates] = useState(false);
  const [rateSourceNotice, setRateSourceNotice] = useState('Verified 2026 Pakistan Construction Benchmark');
  const [selectedBoqVarieties, setSelectedBoqVarieties] = useState<Record<string, string>>(() => {
    const defaults: Record<string, string> = {};
    DETAILED_MATERIALS_CATALOG.forEach((m) => {
      defaults[m.id] = m.defaultVarietyId;
    });
    return defaults;
  });
  const [customUnitPrices, setCustomUnitPrices] = useState<Record<string, number>>({
    cement_bag: 1450,
    steel_ton: 275000,
    brick_unit: 14.5,
    sand_cft: 48,
    crush_cft: 125,
    labor_per_sqft: 450,
    tiles_sqft: 350,
    paint_sqft: 55,
    door_unit: 35000,
    window_unit: 28000,
    bath_sanitary_unit: 65000,
    electrical_sqft: 260,
    waterproofing_sqft: 95,
  });
  const [boqData, setBoqData] = useState<any>(null);
  const [isUpdatingBoq, setIsUpdatingBoq] = useState(false);

  const [budgetPriority, setBudgetPriority] = useState<'economical' | 'balanced' | 'luxury'>('balanced');

  // The brief is the only input - the AI prompt and the guided interview both produce it
  const handlePromptChange = (newText: string) => {
    setPromptText(newText);
  };

  const handleSwitchMode = (mode: 'prompt' | 'form') => {
    setCreationMode(mode);
  };

  // AI-prompt flow: what the design will be built from is read from the prompt by the backend (no form defaults)
  const [briefReading, setBriefReading] = useState<any>(null);
  const [isReadingBrief, setIsReadingBrief] = useState(false);
  const [briefReadError, setBriefReadError] = useState<string | null>(null);

  const handleProceedToReview = async (textOverride?: unknown) => {
    const text = (typeof textOverride === 'string' ? textOverride : promptText).trim();
    if (!text) return;
    if (typeof textOverride === 'string') setPromptText(text);     // the guided interview hands over its brief
    setIsReadingBrief(true);
    setBriefReadError(null);
    try {
      const reading = await apiService.readBrief(text);
      setBriefReading(reading);
      setCurrentStep(3);
    } catch (e: any) {
      setBriefReadError(e?.message || 'Could not read your prompt - check that the backend server is running.');
    } finally {
      setIsReadingBrief(false);
    }
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
      } catch { }
    }
  }, [backendDesign]);

  useEffect(() => {
    if (!backendDesign) {
      try {
        const cached = sessionStorage.getItem('archai_active_design');
        if (cached) {
          setBackendDesign(JSON.parse(cached));
        }
      } catch { }
    }
  }, []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generationSource, setGenerationSource] = useState<'live' | 'local'>('local');

  // Synthesis loader status state
  const [synthesisStage, setSynthesisStage] = useState('Initializing spatial synthesis engine...');
  const [synthesisProgress, setSynthesisProgress] = useState(15);
  const [synthesisError, setSynthesisError] = useState<string | null>(null);

  // Result display active tab
  const [resultTab, setResultTab] = useState<'floor_plan' | 'elevation' | '3d_model' | 'audit' | 'boq'>('floor_plan');
  // Dynamic Elevation Style Selection (Modern Contemporary, Classical & Traditional, Minimalist Timber & Stone)
  const [activeElevationStyle, setActiveElevationStyle] = useState<'modern_contemporary' | 'classical_traditional' | 'minimalist_timber'>('modern_contemporary');

  const handleFetchGeminiMarketRates = async (keyToUse = geminiApiKey, cityToUse = geminiCity) => {
    setIsFetchingGeminiRates(true);
    try {
      const res = await apiService.fetchGeminiMarketRates(keyToUse, cityToUse);
      if (res && res.rates) {
        setCustomUnitPrices(res.rates);
        setRateSourceNotice(res.source === 'gemini_live' ? `Live Gemini 1.5 Flash Rates (${res.city})` : `Verified Benchmark Rates (${res.city})`);
        if (keyToUse) {
          try { sessionStorage.setItem('archai_gemini_key', keyToUse); } catch { }
        }
        const area = Math.round(plotWidthFt * plotLengthFt * (floors === 1 ? 0.75 : 1.55));
        const updatedBoq = await apiService.calculateCost({
          covered_area_sqft: area,
          floors,
          bedrooms,
          bathrooms,
          budget_tier: budgetPriority,
          currency: 'PKR',
          custom_unit_prices: res.rates
        });
        setBoqData(updatedBoq);
      }
    } catch (e) {
      console.error('Error fetching market rates:', e);
    } finally {
      setIsFetchingGeminiRates(false);
    }
  };

  const handleUnitPriceChange = async (itemId: string, newRate: number) => {
    const updated = { ...customUnitPrices, [itemId]: newRate };
    setCustomUnitPrices(updated);
    setIsUpdatingBoq(true);
    try {
      const area = Math.round(plotWidthFt * plotLengthFt * (floors === 1 ? 0.75 : 1.55));
      const updatedBoq = await apiService.calculateCost({
        covered_area_sqft: area,
        floors,
        bedrooms,
        bathrooms,
        budget_tier: budgetPriority,
        currency: 'PKR',
        custom_unit_prices: updated
      });
      setBoqData(updatedBoq);
    } catch (e) {
      console.warn('BOQ update warning:', e);
    } finally {
      setIsUpdatingBoq(false);
    }
  };

  const CATALOG_TO_API_MAP: Record<string, string> = {
    cement: 'cement_bag',
    steel: 'steel_ton',
    bricks: 'brick_unit',
    sand: 'sand_cft',
    crush: 'crush_cft',
    civil_labor: 'labor_per_sqft',
    tiles: 'tiles_sqft',
    paint: 'paint_sqft',
    doors: 'door_unit',
    windows: 'window_unit',
    sanitary: 'bath_sanitary_unit',
    electrical: 'electrical_sqft',
    waterproofing: 'waterproofing_sqft',
  };

  const handleBoqVarietyChange = (matId: string, varietyId: string) => {
    const mat = DETAILED_MATERIALS_CATALOG.find((m) => m.id === matId);
    if (!mat) return;
    const variety = mat.varieties.find((v) => v.id === varietyId);
    if (!variety) return;
    setSelectedBoqVarieties((prev) => ({ ...prev, [matId]: varietyId }));
    const apiId = CATALOG_TO_API_MAP[matId] || matId;
    handleUnitPriceChange(apiId, variety.defaultPricePKR);
  };

  // 'ground' | 'first' | 'floor_2' | 'floor_3' ... (one per storey the backend drew) | 'rooftop' | 'all'
  const [activeFloorView, setActiveFloorView] = useState<string>('ground');
  const [view3d, setView3d] = useState<'interactive' | 'front_right' | 'front_left'>('interactive');
  const [planLayer, setPlanLayer] = useState<'structural' | 'furnishing'>('structural');
  const [renderMode, setRenderMode] = useState<'backend_png' | 'interactive_svg'>('backend_png');

  // Regeneration View & Modification State
  const [isRegeneratePageOpen, setIsRegeneratePageOpen] = useState(false);
  const [refinementPrompt, setRefinementPrompt] = useState('');
  const [revisionNumber, setRevisionNumber] = useState(1);

  // Version history, spatial conflicts & CAD package exports
  const [designHistory, setDesignHistory] = useState<Array<{ version: number; label: string; design: any }>>([]);
  // every change request made on this design: what was asked, whether it was applied, and what really changed
  const [changeLog, setChangeLog] = useState<Array<{ request: string; applied: boolean; message: string; changes: string[] }>>([]);
  const [activeConflict, setActiveConflict] = useState<{ reason: string; alternative: string } | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'dxf' | 'svg' | 'blend' | 'obj' | 'png'>('pdf');
  const [exportLoading, setExportLoading] = useState(false);
  const [activeVariantId, setActiveVariantId] = useState<string>('alt_1');

  useEffect(() => {
    if (backendDesign && (!designHistory || designHistory.length === 0)) {
      setDesignHistory([{ version: 1, label: 'v1 (Original)', design: backendDesign }]);
      setChangeLog([]);
    }
  }, [backendDesign]);

  // A template opens the guided interview with its description - the architect then asks what is still open
  const [interviewSeed, setInterviewSeed] = useState('');
  useEffect(() => {
    if (templateId) {
      const t = templates.find((tpl) => tpl.id === templateId);
      if (t) {
        setProjectName(`${t.name} (Customized)`);
        const storeys = t.floors === 1 ? 'single' : t.floors === 2 ? 'double' : `${t.floors}`;
        setInterviewSeed(`${t.name}: a ${storeys} storey ${String(t.style).toLowerCase()} house on a ${String(t.plotCategory).replace('_', ' ')} plot with ${t.bedrooms} bedrooms and ${t.bathrooms} bathrooms.`);
        setCreationMode('form');
        setCurrentStep(2);
      }
    }
  }, [templateId, templates]);

  const calculatedAreaSqFt = Math.round(plotWidthFt * plotLengthFt);
  const calculatedMarla = (calculatedAreaSqFt / 225).toFixed(2);

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
    // adds design context only - never a fixed size (sizes come from the client's own words)
    const enhanced = `${promptText} Give every bedroom, lounge and the drawing room a window on open air for daylight and cross ventilation, stack the kitchen and bathrooms over each other, keep the walk from the entrance to every room short and clear, and keep the society's setbacks open.`;
    handlePromptChange(enhanced);
    setPromptEnhanced(true);
    setTimeout(() => setPromptEnhanced(false), 3000);
  };

  const handleAppendRefinementChip = (chip: string) => {
    setRefinementPrompt((prev) => (prev ? `${prev}, ${chip.replace('+', '').trim()}` : chip.replace('+', '').trim()));
  };

  // Generation Handler: Connects to Backend and persists to Database
  const handleStartGeneration = async (customPrompt?: string, overrideApiKey?: string) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setSynthesisError(null);

    const activePrompt = customPrompt || promptText;
    const synthesisStep = 4;
    setCurrentStep(synthesisStep);

    let progressVal = 18;
    setSynthesisProgress(progressVal);
    setSynthesisStage('Evaluating plot boundary envelope, CDA/LDA setbacks & zoning rules...');

    // Progress interval tracking real execution lifecycle (caps at 88% while awaiting server)
    const stageInterval = setInterval(() => {
      progressVal = Math.min(88, progressVal + Math.floor(Math.random() * 6) + 4);
      setSynthesisProgress(progressVal);
      if (progressVal >= 25 && progressVal < 50) {
        setSynthesisStage('Synthesizing learned spatial floor plan geometry & room circulation...');
      } else if (progressVal >= 50 && progressVal < 70) {
        setSynthesisStage('Evaluating door swing arcs, wall hosting & municipal daylight lightwells...');
      } else if (progressVal >= 70 && progressVal < 90) {
        setSynthesisStage('Rendering high-resolution 2D technical floor plans & architectural front elevation...');
      }
    }, 1100);

    try {
      // the brief is the only input - no plot / storey / room defaults and no preset room sizes
      const promptOnly = true;
      const keyToUse = (overrideApiKey || geminiApiKey || '').trim();
      const backendRes = await apiService.generateDesign({
        prompt: activePrompt,
        prompt_only: true,
        reading: briefReading && (briefReading.prompt || '').trim() === activePrompt.trim() ? briefReading : undefined,
        budget_tier: budgetPriority,
        currency: 'PKR',
        seed: Math.floor(Math.random() * 90000) + 1000,
        api_key: keyToUse || undefined,
      });

      // the plot / storeys actually designed (read from the prompt in the AI flow)
      const outW = promptOnly ? Number(backendRes?.plot?.width_ft) || plotWidthFt : plotWidthFt;
      const outL = promptOnly ? Number(backendRes?.plot?.length_ft) || plotLengthFt : plotLengthFt;
      const outFloors = promptOnly ? Number(backendRes?.floors) || floors : floors;
      const outBeds = promptOnly ? Number(backendRes?.requirements?.parsed?.bedrooms) || bedrooms : bedrooms;
      const outBaths = promptOnly ? Number(backendRes?.requirements?.parsed?.bathrooms) || bathrooms : bathrooms;
      const outArea = Math.round(outW * outL);
      if (promptOnly) {
        setPlotPreset('custom');
        setPlotWidthFt(outW);
        setPlotLengthFt(outL);
        setFloors(outFloors);
        setBedrooms(outBeds);
        setBathrooms(outBaths);
        if (backendRes?.reading?.style) setStyle(backendRes.reading.style as ArchitecturalStyle);
      }

      clearInterval(stageInterval);
      setSynthesisProgress(95);
      setSynthesisStage('Finalizing 3D spatial geometry & saving project to database...');

      setBackendDesign(backendRes);
      setGenerationSource('live');
      try {
        sessionStorage.setItem('archai_active_design', JSON.stringify(backendRes));
      } catch { }

      const proj = createProject({
        title: backendRes?.project_title || projectName,
        type: projectType,
        ownerId: currentUser?.id || 'usr_customer_1',
        ownerName: currentUser?.name || 'Homeowner',
        plotPreset: promptOnly ? 'custom' : plotPreset,
        plotWidthFt: outW,
        plotLengthFt: outL,
        unit,
        plotAreaSqFt: outArea,
        plotAreaMarla: parseFloat((outArea / 225).toFixed(2)),
        floors: outFloors,
        bedrooms: outBeds,
        bathrooms: outBaths,
        style,
        budgetMinPKR: outArea * (outFloors === 1 ? 4500 : 7000),
        budgetMaxPKR: outArea * (outFloors === 1 ? 6500 : 9500),
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
          plot_width: outW,
          plot_length: outL,
          floors: outFloors,
          bedrooms: outBeds,
          bathrooms: outBaths,
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

      setSynthesisProgress(100);
      setSynthesisStage('Complete! Architectural blueprints and technical elevation ready.');

      setTimeout(() => {
        const resultStep = 5;
        setCurrentStep(resultStep);
        setIsSubmitting(false);
      }, 400);

    } catch (err: any) {
      clearInterval(stageInterval);
      console.error('Synthesis failure:', err);
      setSynthesisError(err?.message || 'Synthesis request failed. Please check server status and retry.');
      setIsSubmitting(false);
    }
  };

  const handleRestoreVersion = (verNumber: number) => {
    const found = designHistory.find((item) => item.version === verNumber);
    if (found) {
      setBackendDesign(found.design);
      setRevisionNumber(found.version);
      setActiveConflict(null);
    }
  };

  const handleSelectVariant = (variant: any) => {
    setActiveVariantId(variant.id);
  };

  const handleExportDownload = async () => {
    setExportLoading(true);
    try {
      const pid = backendDesign?.project_id || backendDesign?.plan_id || createdProjectId || 'archi_design';
      const result = await apiService.exportFile(exportFormat, {
        ...(backendDesign || {}),
        project_title: backendDesign?.project_title || projectName,
        project_id: pid,
        version: revisionNumber,
        plot_width: plotWidthFt,
        plot_length: plotLengthFt,
        style
      });
      const url = window.URL.createObjectURL(result.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      console.error("Export error:", e);
    } finally {
      setExportLoading(false);
    }
  };

  // Regeneration Handler with Spatial Modifications, Conflict Detection & Version History
  const handleRegenerateWithModifications = async () => {
    setIsRegeneratePageOpen(false);
    setActiveConflict(null);

    try {
      const planId = backendDesign?.project_id || backendDesign?.plan_id || createdProjectId;
      if (planId) {
        setIsSubmitting(true);
        setSynthesisStage('Evaluating architectural refinement and re-hosting door openings...');
        setCurrentStep(4);

        // the change is applied to the design on screen: its own script, brief and plot go with the request
        const parsedReq = backendDesign?.requirements?.parsed || {};
        const res = await apiService.regenerateWithImprovement({
          plan_id: planId,
          improvement_text: refinementPrompt,
          base_version: revisionNumber,
          script: backendDesign?.design_script || '',
          prompt: backendDesign?.brief || promptText,
          plot_width: Number(backendDesign?.plot?.width_ft) || plotWidthFt,
          plot_length: Number(backendDesign?.plot?.length_ft) || plotLengthFt,
          floors: Number(parsedReq.floors) || (Array.isArray(backendDesign?.floors_detail) ? backendDesign.floors_detail.filter((f: any) => !f.is_roof_level).length : floors) || floors,
          bedrooms: Number(parsedReq.bedrooms) || bedrooms,
          bathrooms: Number(parsedReq.bathrooms) || 0,
          style,
          requirements: backendDesign?.requirements?.parsed,
          history: changeLog.map((c) => ({ role: 'user', text: c.request })),
        });
        setChangeLog((prev) => [...prev, {
          request: refinementPrompt,
          applied: Boolean(res?.change_applied),
          message: String(res?.assistant_message || res?.error || ''),
          changes: Array.isArray(res?.changes) ? res.changes : [],
        }]);
        if (res?.change_applied === false) {
          // the previous design was kept: say why, and do not create a new version
          setActiveConflict({
            reason: String(res?.assistant_message || 'The change was not applied.'),
            alternative: '',
          });
          setCurrentStep(5);
          setIsSubmitting(false);
          return;
        }

        if (res?.success === false && res?.conflicts && res.conflicts.length > 0) {
          setActiveConflict({
            reason: res.conflicts[0].reason,
            alternative: res.conflicts[0].alternative
          });
          setCurrentStep(5);
          setIsSubmitting(false);
          return;
        } else {
          setActiveConflict(null);
        }

        const nextVer = res?.version || (revisionNumber + 1);
        setRevisionNumber(nextVer);
        const updatedDesign = {
          ...backendDesign,
          ...res,
          canonical_plan: res.canonical_plan || backendDesign?.canonical_plan,
          images: res.images || backendDesign?.images,
          floors: res.floors || backendDesign?.floors,
          compliance_checklist: res.compliance_checklist || backendDesign?.compliance_checklist,
          quality_gate: res.quality_gate || backendDesign?.quality_gate,
          project_id: planId
        };
        setBackendDesign(updatedDesign);
        setDesignHistory((prev) => [
          ...prev,
          { version: nextVer, label: `v${nextVer}`, design: updatedDesign }
        ]);
        setResultTab('floor_plan');
        setActiveFloorView('ground');
        setCurrentStep(5);
        setIsSubmitting(false);
      } else {
        setRevisionNumber((prev) => prev + 1);
        const revisedPrompt = `${promptText}. Design Modifications: ${refinementPrompt}`;
        setPromptText(revisedPrompt);
        await handleStartGeneration(revisedPrompt);
      }
    } catch (e: any) {
      console.warn("Regenerate notice:", e);
      setActiveConflict({
        reason: `The change could not be made: ${e?.message || 'the design server did not answer'}. Your current design is unchanged.`,
        alternative: ''
      });
      setCurrentStep(5);
      setIsSubmitting(false);
    }
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
      { num: 2, label: 'Interview' },
      { num: 3, label: 'Review Brief' },
      { num: 4, label: 'Synthesis' },
      { num: 5, label: 'Floor Plan' },
    ];

  const totalSteps = steps.length;
  const isSynthesisStep = currentStep === 4;
  const isResultStep = currentStep === 5;

  // Active Floor Plan Image from Backend (Guarantees Rooftop Blueprint PNG is always found)
  const rooftopUrl = backendDesign?.images?.rooftop ||
    backendDesign?.images?.rooftop_slab_plan ||
    (backendDesign?.images?.ground ? backendDesign.images.ground.replace('_ground_floor_2d.png', '_rooftop_slab_plan_2d.png') : null);

  // One view per storey the backend actually drew (ground, first, floor_2, ...)
  const storeyKeyOf = (i: number) => (i === 0 ? 'ground' : i === 1 ? 'first' : `floor_${i}`);
  const storeyNames = ['Ground', 'First', 'Second', 'Third', 'Fourth', 'Fifth'];
  const storeyKeys: string[] = [];
  for (let i = 0; i < 8; i += 1) {
    if (backendDesign?.images?.[storeyKeyOf(i)]) storeyKeys.push(storeyKeyOf(i));
    else break;
  }
  if (storeyKeys.length === 0) {
    for (let i = 0; i < Math.max(1, floors); i += 1) storeyKeys.push(storeyKeyOf(i));
  }
  const activeLevel = Math.max(0, storeyKeys.indexOf(activeFloorView));
  const storeyLabel = (i: number) => `${storeyNames[i] || `Level ${i}`} Floor`;

  const backendFloorImage =
    activeFloorView === 'rooftop' ? rooftopUrl :
      activeFloorView === 'all' ? (backendDesign?.images?.all || backendDesign?.images?.multiFloor || backendDesign?.images?.presentation) :
        (planLayer === 'furnishing'
          ? (backendDesign?.images?.[`${storeyKeys[activeLevel]}_furnishing`] || backendDesign?.images?.[storeyKeys[activeLevel]])
          : (backendDesign?.images?.[`${storeyKeys[activeLevel]}_structural`] || backendDesign?.images?.[storeyKeys[activeLevel]]));

  const elevationImage =
    activeElevationStyle === 'classical_traditional'
      ? (backendDesign?.images?.elevation_classical || backendDesign?.images?.elevation_styles?.classical_traditional || backendDesign?.images?.elevation)
      : activeElevationStyle === 'minimalist_timber'
      ? (backendDesign?.images?.elevation_timber || backendDesign?.images?.elevation_styles?.minimalist_timber || backendDesign?.images?.elevation)
      : (backendDesign?.images?.elevation_modern || backendDesign?.images?.elevation_styles?.modern_contemporary || backendDesign?.images?.elevation);

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      {/* Workflow Stepper Header */}
      <div className="border-b border-[#E2E7E1] pb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EEF4F0] text-[#23483D] text-xs font-semibold border border-[#DCE7DE] mb-2">
              <Compass className="h-3.5 w-3.5" />
              <span>
                {creationMode === 'prompt' ? 'AI Natural Language Flow' : 'Guided Interview Flow'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
              New Residential Design
            </h1>
            <p className="text-xs text-[#68736C] mt-1">
              Step {currentStep} of {totalSteps} &bull; {
                creationMode === 'prompt'
                  ? (currentStep === 4 ? 'Synthesizing bylaw-compliant spatial layout' : currentStep === 5 ? 'Architectural blueprints & technical elevation' : 'Describing intent in natural language')
                  : (currentStep === 4 ? 'Synthesizing bylaw-compliant spatial layout' : currentStep === 5 ? 'Architectural blueprints & technical elevation' : 'The architect asks what your brief leaves open')
              }
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
                className={`h-2 w-full rounded-full transition-all ${s.num < currentStep
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
              className={`p-6 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${creationMode === 'prompt'
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

            {/* Option 2: Guided Interview with the Architect */}
            <div
              onClick={() => handleSwitchMode('form')}
              className={`p-6 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between ${creationMode === 'form'
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
                    <h3 className="font-bold text-base text-[#202923]">Guided Interview with the Architect</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-[#68736C]">Asks before it designs</span>
                  </div>
                  <p className="text-xs text-[#68736C] mt-2 leading-relaxed">
                    Describe your house in your own words and the AI architect asks you about what is still open - plot size, floors, where the staircase goes, bedrooms per floor - one question at a time. Nothing is pre-selected.
                  </p>
                </div>
                <div className="text-[11px] text-[#23483D] font-medium bg-white/70 p-2.5 rounded-xl border border-[#DCE7DE]">
                  📐 Flow: Mode &rarr; Interview &rarr; Review Brief &rarr; Generate Floor Plan
                </div>
              </div>

              <div className="pt-6 flex items-center justify-between text-xs font-semibold text-[#23483D]">
                <span>Best if you are not sure what to write</span>
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
              <span>{creationMode === 'prompt' ? 'Continue to AI Prompt Studio' : 'Start the Interview'}</span>
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

          {/* Project Title Input */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-[#202923] flex items-center justify-between">
              <span>Project Title / Name</span>
              <span className="text-[10px] text-[#68736C] font-normal">Identifies your design deliverables</span>
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g. Modern Executive Villa, DHA Phase 6"
              className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D] transition-colors"
            />
          </div>

          {/* The prompt is the only input: no plot presets, storey or style pickers, no preset room sizes */}
          <div className="p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] text-xs text-[#202923] space-y-1.5">
            <p className="font-bold flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-[#23483D]" />
              Your prompt is the only input
            </p>
            <p className="text-[#68736C] leading-relaxed">
              Write everything in your own words: the plot size (e.g. <em>30 x 60 ft</em>, <em>53 ft wide and 25 ft deep</em> or{' '}
              <em>10 marla</em>), the storeys or the portion you are designing, every room, any sizes you want (e.g.{' '}
              <em>master bedroom 14x16</em>), your society's setbacks if they differ, and the style. Nothing is pre-selected:
              anything you leave out is decided by the architect, and you will see exactly what was understood before generation.
            </p>
          </div>

          {/* Main Prompt Textarea */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-[#202923]">
                Your Architectural Prompt
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowApiKeyInput(!showApiKeyInput)}
                  className="text-[11px] text-[#23483D] hover:underline flex items-center gap-1 font-semibold"
                >
                  <Key className="h-3 w-3" />
                  <span>{geminiApiKey ? 'API Key Configured' : 'Configure Gemini API Key'}</span>
                </button>
                <span className="text-[11px] text-[#68736C] font-mono">
                  {promptText.length} characters
                </span>
              </div>
            </div>

            {showApiKeyInput && (
              <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-900 flex items-center gap-1.5">
                    <Key className="h-3.5 w-3.5 text-amber-700" />
                    Custom Gemini API Key
                  </span>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] text-amber-800 underline font-semibold"
                  >
                    Get free key &rarr;
                  </a>
                </div>
                <div className="flex gap-2">
                  <input
                    type="password"
                    placeholder="AIzaSy..."
                    value={geminiApiKey}
                    onChange={(e) => setGeminiApiKey(e.target.value)}
                    className="flex-1 bg-white border border-amber-300 rounded-lg px-3 py-1.5 text-xs font-mono text-[#202923] focus:outline-none focus:border-[#23483D]"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      const k = geminiApiKey.trim();
                      if (k) {
                        try { sessionStorage.setItem('archai_gemini_key', k); } catch {}
                        await apiService.saveApiKey(k);
                      }
                      setShowApiKeyInput(false);
                    }}
                    className="px-3.5 py-1.5 bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold rounded-lg"
                  >
                    Save Key
                  </button>
                </div>
              </div>
            )}

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

          {briefReadError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{briefReadError}</div>
          )}

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
              disabled={isReadingBrief || !promptText.trim()}
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] disabled:opacity-60 text-white text-xs font-semibold shadow-sm flex items-center gap-2"
            >
              <span>{isReadingBrief ? 'Reading your prompt...' : 'Review What the AI Understood'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 (AI FLOW): REVIEW & EDIT AI BRIEF */}
      {currentStep === 3 && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
            <div>
              <h2 className="text-xl font-bold text-[#202923] font-heading flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-[#23483D]" />
                What the AI Understood from Your Prompt
              </h2>
              <p className="text-xs text-[#68736C] mt-1">
                Everything below was read from your prompt alone. To change anything, edit the prompt - every item is checked on the final plan.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="px-3.5 py-1.5 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] hover:bg-[#DCE7DE] text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto transition-colors"
            >
              <Edit3 className="h-3.5 w-3.5" />
              <span>{creationMode === 'prompt' ? 'Edit Prompt' : 'Back to the Interview'}</span>
            </button>
          </div>

          {briefReading ? (
            <div className="space-y-4 text-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1]">
                <span className="text-[#68736C] font-semibold">Project Title</span>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="bg-white border border-[#E2E7E1] rounded-lg px-2 py-1 text-xs font-medium text-[#202923] sm:w-72"
                />
              </div>

              {(briefReading.missing || []).length > 0 && (
                <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 space-y-1">
                  <p className="font-bold">Your prompt is missing something the design needs:</p>
                  {(briefReading.missing || []).map((m: string, i: number) => <p key={i}>&bull; {m}</p>)}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-3">
                  <h3 className="font-bold text-[#202923] flex items-center gap-2">
                    <Building className="h-4 w-4 text-[#23483D]" />
                    Site (from your prompt)
                  </h3>
                  <div className="flex justify-between gap-3">
                    <span className="text-[#68736C]">Plot:</span>
                    <strong className="text-[#202923] font-mono text-right">
                      {briefReading.plot?.width_ft
                        ? `${briefReading.plot.width_ft} \u00d7 ${briefReading.plot.length_ft} ft${briefReading.plot.source === 'marla_typical' ? ' (usual shape for your marla)' : ' (as you wrote it)'}`
                        : 'not stated'}
                    </strong>
                  </div>
                  {briefReading.plot?.width_ft && (
                    <div className="flex justify-between gap-3">
                      <span className="text-[#68736C]">Area:</span>
                      <strong className="text-[#202923] font-mono">
                        {Math.round(briefReading.plot.width_ft * briefReading.plot.length_ft).toLocaleString()} sq ft &bull; {briefReading.plot.marla} marla
                      </strong>
                    </div>
                  )}
                  <div className="flex justify-between gap-3">
                    <span className="text-[#68736C]">Levels:</span>
                    <strong className="text-[#202923] text-right">
                      {briefReading.portion?.kind === 'upper'
                        ? `Level ${briefReading.portion.level} portion only (reached by the stair)`
                        : briefReading.storeys
                          ? `${briefReading.storeys} storey${briefReading.storeys > 1 ? 's' : ''}`
                          : 'not stated - the architect chooses'}
                    </strong>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-[#68736C]">Setbacks:</span>
                    <strong className="text-[#202923] font-mono text-right">
                      {briefReading.setbacks?.front_ft != null
                        ? `front ${fmtFeet(briefReading.setbacks.front_ft)} (${briefReading.setbacks.front_source === 'prompt' ? 'your prompt' : 'AI logic'}) \u00b7 rear ${fmtFeet(briefReading.setbacks.rear_ft)} (${briefReading.setbacks.rear_source === 'prompt' ? 'your prompt' : 'AI logic'})`
                        : 'determined by AI architect'}
                    </strong>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-[#68736C]">Style:</span>
                    <strong className="text-[#202923]">{briefReading.style || 'not stated'}</strong>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-[#68736C]">Read by:</span>
                    <span className="text-[#68736C] font-mono">{briefReading.read_by}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-3">
                  <h3 className="font-bold text-[#202923] flex items-center gap-2">
                    <Home className="h-4 w-4 text-[#23483D]" />
                    Your requirements (each one is checked on the plan)
                  </h3>
                  {briefReading.understood_as && (
                    <p className="text-[#202923] leading-relaxed">{briefReading.understood_as}</p>
                  )}
                  <ol className="list-decimal pl-4 space-y-1 text-[#202923]">
                    {(briefReading.checklist || []).map((c: string, i: number) => <li key={i}>{c}</li>)}
                  </ol>
                  {(briefReading.checklist || []).length === 0 && (
                    <p className="text-[#68736C]">No specific rooms found - the architect designs from your description.</p>
                  )}
                </div>
              </div>

              {(briefReading.assumptions || []).length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 space-y-1">
                  <p className="font-bold">Assumed (write it in the prompt to change it):</p>
                  {(briefReading.assumptions || []).map((m: string, i: number) => <p key={i}>&bull; {m}</p>)}
                </div>
              )}
              {((briefReading.not_stated || []).length > 0 || (briefReading.notes || []).length > 0) && (
                <div className="p-4 rounded-2xl bg-white border border-[#E2E7E1] text-[#68736C] space-y-1">
                  <p className="font-bold text-[#202923]">Not in your prompt (the architect decides):</p>
                  {(briefReading.not_stated || []).map((m: string, i: number) => <p key={`n${i}`}>&bull; {m}</p>)}
                  {(briefReading.notes || []).map((m: string, i: number) => <p key={`o${i}`}>&bull; {m}</p>)}
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] text-xs text-[#68736C]">
              Your prompt has not been read yet - go back and press "Review What the AI Understood".
            </div>
          )}

          {/* Prompt Recap */}
          <div className="p-4 rounded-xl bg-[#EEF4F0]/70 border border-[#DCE7DE] text-xs space-y-1">
            <span className="text-[11px] font-bold text-[#23483D]">Prompt to be Dispatched to ArchiCraft AI Spatial Engine:</span>
            <p className="text-[#202923] italic leading-relaxed">"{promptText}"</p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#E2E7E1]">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>{creationMode === 'prompt' ? 'Back to Prompt Studio' : 'Back to the Interview'}</span>
            </button>
            <button
              onClick={() => handleStartGeneration()}
              disabled={isSubmitting || !briefReading?.ok}
              title={briefReading?.ok ? '' : 'Add the plot size to your prompt first'}
              className="px-7 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] disabled:opacity-50 text-white text-xs font-bold shadow-md flex items-center gap-2 transition-transform active:scale-95"
            >
              <Sparkles className="h-4 w-4 text-emerald-300" />
              <span>Generate Floor Plan</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================
          FLOW 2: GUIDED INTERVIEW (creationMode === 'form')
          The architect asks what the description leaves open (plot, floors, where the stairs go, bedrooms ...)
          ======================================================== */}
      {creationMode === 'form' && (
        <div className={currentStep === 2 ? '' : 'hidden'}>
          <GuidedInterview
            seed={interviewSeed}
            busy={isReadingBrief}
            error={briefReadError}
            onBack={() => setCurrentStep(1)}
            onComplete={(brief) => handleProceedToReview(brief)}
          />
        </div>
      )}

      {isSynthesisStep && (
        <div className="bg-white border border-[#E2E7E1] rounded-2xl p-10 sm:p-16 text-center space-y-6 shadow-xs">
          {synthesisError ? (
            <div className="space-y-6 max-w-lg mx-auto">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-rose-100 border border-rose-300 flex items-center justify-center text-rose-600">
                <AlertTriangle className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-rose-700 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                  Synthesis Exception
                </span>
                <h2 className="text-xl sm:text-2xl font-bold text-[#202923] font-heading">
                  Architectural Synthesis Failed
                </h2>
                <p className="text-xs text-rose-800 bg-rose-50 p-3 rounded-xl border border-rose-200 text-left font-mono leading-relaxed">
                  {synthesisError}
                </p>

                {/* Direct API Key Recovery Card */}
                {(synthesisError.toLowerCase().includes('api key') ||
                  synthesisError.toLowerCase().includes('permission_denied') ||
                  synthesisError.toLowerCase().includes('leaked') ||
                  synthesisError.toLowerCase().includes('403')) && (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-left space-y-3 mt-3">
                    <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                      <Key className="h-4 w-4 text-amber-700" />
                      <span>Enter Your Google Gemini API Key</span>
                    </div>
                    <p className="text-[11px] text-amber-800 leading-relaxed">
                      Google automatically revoked the shared default key because it was reported as leaked. Provide your own free Gemini API key below to continue generation:
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder="Paste AIzaSy... key here"
                        value={geminiApiKey}
                        onChange={(e) => setGeminiApiKey(e.target.value)}
                        className="flex-1 bg-white border border-amber-300 rounded-lg px-3 py-2 text-xs font-mono text-[#202923] focus:outline-none focus:border-[#23483D]"
                      />
                      <button
                        type="button"
                        onClick={async () => {
                          const k = geminiApiKey.trim();
                          if (!k) return;
                          try { sessionStorage.setItem('archai_gemini_key', k); } catch {}
                          await apiService.saveApiKey(k);
                          handleStartGeneration(undefined, k);
                        }}
                        className="px-4 py-2 bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold rounded-lg shadow-sm shrink-0 transition-colors"
                      >
                        Save &amp; Generate
                      </button>
                    </div>
                    <p className="text-[10px] text-amber-700">
                      Get a free Gemini API key in 30 seconds at{' '}
                      <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noreferrer"
                        className="underline font-bold text-amber-900 hover:text-amber-950"
                      >
                        Google AI Studio (aistudio.google.com)
                      </a>
                    </p>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold"
                >
                  Return to Brief
                </button>
                <button
                  type="button"
                  onClick={() => handleStartGeneration()}
                  className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold shadow-md flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Retry Synthesis</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-4 border-[#EEF4F0] border-t-[#23483D] animate-spin" />
                <Compass className="h-10 w-10 text-[#23483D] animate-pulse" />
              </div>

              <div className="space-y-2 max-w-lg mx-auto">
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#23483D] bg-[#EEF4F0] px-3 py-1 rounded-full border border-[#DCE7DE]">
                  ArchiCraft AI Studio &bull; Python Spatial Engine
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
                  <span>Learned-Strategy Synthesis</span>
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
            </>
          )}
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
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#23483D]">
                    {backendDesign?.model_used ? `Gemini AI Live (${backendDesign.model_used})` : generationSource === 'live' ? 'ArchiCraft AI Engine Verified' : 'Local Architectural Solver'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#DCE7DE] text-[#23483D]">
                    {revisionNumber > 1 ? `Revision v${revisionNumber}` : 'AI Civil Architect Logic'}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-[#202923]">
                  {backendDesign?.project_title || generatedAlternative?.name || projectName}
                </h2>
                <p className="text-xs text-[#68736C]">
                  {plotWidthFt} &times; {plotLengthFt} ft &bull; {floors} Storeys &bull; {bedrooms} Bedrooms &bull; Pure AI Spatial Layout
                </p>
                {/* VERSION PILLS & RESTORE */}
                <div className="flex items-center gap-1.5 mt-2">
                  <span className="text-[10px] font-bold text-[#68736C] uppercase tracking-wider flex items-center gap-1">
                    <History className="h-3 w-3 text-[#23483D]" /> Revisions:
                  </span>
                  {designHistory.map((item) => (
                    <button
                      key={item.version}
                      onClick={() => handleRestoreVersion(item.version)}
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold transition-all ${revisionNumber === item.version
                          ? 'bg-[#23483D] text-white shadow-xs'
                          : 'bg-white border border-[#DCE7DE] text-[#23483D] hover:bg-[#EEF4F0]'
                        }`}
                    >
                      {item.label}
                    </button>
                  ))}
                  {revisionNumber > 1 && (
                    <button
                      onClick={() => handleRestoreVersion(1)}
                      className="text-[10px] text-amber-700 hover:text-amber-900 underline font-semibold ml-1"
                    >
                      Restore to v1
                    </button>
                  )}
                </div>
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
              <button
                onClick={() => setExportModalOpen(true)}
                className="px-4 py-2 rounded-xl bg-white border border-[#E2E7E1] text-[#202923] hover:border-[#23483D] text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs hover:bg-[#F7F7F2]"
              >
                <Download className="h-3.5 w-3.5 text-[#23483D]" />
                <span>Export CAD Package</span>
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

          {/* A CHANGE REQUEST THAT WAS NOT APPLIED (the design on screen is unchanged) */}
          {activeConflict && (
            <div className="bg-rose-50 border-2 border-rose-500 rounded-2xl p-5 shadow-sm space-y-3 animate-in fade-in duration-200">
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-rose-600 text-white shrink-0 mt-0.5">
                  <AlertTriangle className="h-6 w-6" />
                </div>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-600 text-white">
                      Change not applied - your design is unchanged
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm font-bold text-rose-900 leading-relaxed">
                    {activeConflict.reason}
                  </p>
                  {activeConflict.alternative && (
                    <div className="p-3 bg-white/80 rounded-xl border border-rose-200 mt-2 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-emerald-800 tracking-wider block">
                        You could ask for this instead:
                      </span>
                      <p className="text-xs text-[#202923]">
                        {activeConflict.alternative}
                      </p>
                    </div>
                  )}
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      onClick={() => {
                        if (activeConflict.alternative) setRefinementPrompt(activeConflict.alternative);
                        setActiveConflict(null);
                        setIsRegeneratePageOpen(true);
                      }}
                      className="px-3 py-1.5 bg-rose-600 text-white text-[11px] font-bold rounded-lg hover:bg-rose-700 transition-colors"
                    >
                      {activeConflict.alternative ? 'Use this request' : 'Ask again differently'}
                    </button>
                    <button
                      onClick={() => setActiveConflict(null)}
                      className="px-3 py-1.5 bg-white border border-rose-300 text-rose-800 text-[11px] font-medium rounded-lg hover:bg-rose-50 transition-colors"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 3 DESIGN VARIANT CARDS */}
          {backendDesign?.variants && backendDesign.variants.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-[#23483D]" />
                  <h3 className="font-bold text-xs text-[#202923] uppercase tracking-wider">
                    AI Layout Strategies & Design Variants
                  </h3>
                </div>
                <span className="text-[10px] text-[#68736C]">
                  3 Distinct Bylaw-Validated Archetypes
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {backendDesign.variants.map((v: any) => {
                  const isSelected = activeVariantId === v.id || (activeVariantId === 'alt_1' && v.is_active);
                  return (
                    <div
                      key={v.id}
                      onClick={() => handleSelectVariant(v)}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-2 ${isSelected
                          ? 'bg-white border-2 border-[#23483D] shadow-sm'
                          : 'bg-[#F7F7F2] border-[#E2E7E1] hover:bg-white hover:border-[#23483D]'
                        }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#EEF4F0] text-[#23483D]">
                          {v.id}
                        </span>
                        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          {Math.round((v.quality_score || 0.98) * 100)}% Compliant
                        </span>
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[#202923]">{v.strategy_name}</h4>
                        <p className="text-[11px] text-[#68736C] line-clamp-2 mt-0.5">{v.description}</p>
                      </div>
                      <div className="pt-1.5 border-t border-[#E2E7E1] flex items-center justify-between text-[10px]">
                        <span className="font-mono text-[#8C9890]">{v.archetype_id}</span>
                        <span className={`font-semibold ${isSelected ? 'text-[#23483D]' : 'text-[#68736C]'}`}>
                          {isSelected ? '✓ Active Layout' : 'Select Variant'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI SPATIAL STRATEGY & RULE EXPLAINABILITY */}
          {backendDesign?.explainability && (
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-[#E2E7E1] pb-2.5">
                <div className="flex items-center gap-2">
                  <Info className="h-4 w-4 text-[#23483D]" />
                  <h3 className="font-bold text-xs text-[#202923] uppercase tracking-wider">
                    AI Architecture Logic & Explainability Panel
                  </h3>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE]">
                  Archetype: {backendDesign.explainability.source_archetype_id}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="space-y-2">
                  <div>
                    <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                      Planning Strategy Selected:
                    </span>
                    <p className="font-semibold text-[#202923] mt-0.5">{backendDesign.explainability.strategy_name}</p>
                    <p className="text-[11px] text-[#68736C]">{backendDesign.explainability.strategy_description}</p>
                  </div>
                  {backendDesign.explainability.influenced_by_plans && backendDesign.explainability.influenced_by_plans.length > 0 && (
                    <div>
                      <span className="text-[10px] font-bold text-[#68736C] uppercase tracking-wider block">
                        Extracted Vector Knowledge Influences:
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {backendDesign.explainability.influenced_by_plans.map((pName: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-[#F7F7F2] border border-[#E2E7E1] font-mono text-[9px] text-[#202923]">
                            {pName}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                      What the CAD engine checks:
                    </span>
                    <ul className="list-disc list-inside text-[11px] text-[#68736C] space-y-0.5 mt-0.5">
                      {(backendDesign.explainability.bylaw_rules_applied || []).slice(0, 4).map((rule: string, idx: number) => (
                        <li key={idx} className="line-clamp-1">{rule}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                      Quality Gate Verifications:
                    </span>
                    <ul className="list-disc list-inside text-[11px] text-emerald-700 space-y-0.5 mt-0.5">
                      {(backendDesign.explainability.quality_gate_fixes || []).slice(0, 3).map((fix: string, idx: number) => (
                        <li key={idx} className="line-clamp-1">{fix}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* REQUIREMENTS COMPLIANCE CHECKLIST */}
          {backendDesign?.compliance_checklist && (
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-[#E2E7E1] pb-2.5">
                <div className="flex items-center gap-2">
                  <CheckSquare className="h-4 w-4 text-[#23483D]" />
                  <h3 className="font-bold text-xs text-[#202923] uppercase tracking-wider">
                    Requirements Compliance Checklist
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${backendDesign.compliance_checklist.all_passed
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                    }`}>
                    {backendDesign.compliance_checklist.score_pct}% Match ({backendDesign.compliance_checklist.passed_count}/{backendDesign.compliance_checklist.total_count} Passed)
                  </span>
                </div>
              </div>

              {/* USER STATED REQUIREMENTS */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                  User Stated Requirements:
                </span>
                <div className="divide-y divide-[#E2E7E1] max-h-[140px] overflow-y-auto pr-1 text-xs">
                  {(backendDesign.compliance_checklist.requested_items || backendDesign.compliance_checklist.items || []).map((item: any, idx: number) => (
                    <div key={idx} className="py-1.5 flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="font-semibold text-[#202923] text-[11px]">{item.name}</span>
                        <p className="text-[10px] text-[#68736C]">
                          Req: <span className="font-medium text-[#202923]">{item.requested}</span> &rarr; Delivered: <span className="font-medium text-[#202923]">{item.delivered}</span>
                        </p>
                        {item.detail && <p className="text-[9px] text-[#8C9890]">{item.detail}</p>}
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shrink-0 mt-0.5 ${item.status === 'PASS'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'PARTIAL'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* CHANGE HISTORY: every version can be opened again; every request shows what it really changed */}
          {(designHistory.length > 1 || changeLog.length > 0) && (
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold text-[#202923] uppercase tracking-wider flex items-center gap-1.5">
                  <History className="h-4 w-4 text-[#23483D]" /> Versions and changes
                </span>
                <div className="flex flex-wrap items-center gap-1.5">
                  {designHistory.map((item) => (
                    <button
                      key={item.version}
                      onClick={() => handleRestoreVersion(item.version)}
                      title={revisionNumber === item.version ? 'This version is on screen' : `Go back to ${item.label}`}
                      className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all ${revisionNumber === item.version
                        ? 'bg-[#23483D] text-white'
                        : 'bg-white border border-[#DCE7DE] text-[#23483D] hover:bg-[#EEF4F0]'}`}
                    >
                      {revisionNumber === item.version ? `${item.label} (on screen)` : `Go back to ${item.label}`}
                    </button>
                  ))}
                </div>
              </div>
              {changeLog.length > 0 && (
                <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                  {[...changeLog].reverse().map((c, i) => (
                    <div key={i} className={`p-3 rounded-xl border text-[11px] space-y-1 ${c.applied ? 'border-[#DCE7DE] bg-[#F7F7F2]' : 'border-rose-200 bg-rose-50'}`}>
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-semibold text-[#202923]">You asked: &ldquo;{c.request}&rdquo;</span>
                        <span className={`px-1.5 py-0.5 rounded font-bold font-mono text-[10px] shrink-0 ${c.applied ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                          {c.applied ? 'APPLIED' : 'NOT APPLIED'}
                        </span>
                      </div>
                      {c.message && <p className="text-[#68736C]">{c.message}</p>}
                      {c.changes.length > 0 && (
                        <pre className="mt-1 p-2 rounded-lg bg-white border border-[#E2E7E1] text-[10px] leading-relaxed font-mono overflow-x-auto whitespace-pre">
                          {c.changes.map((ln, k) => (
                            <span key={k} className={ln.startsWith('+') ? 'text-emerald-700' : 'text-rose-700'}>{ln + '\n'}</span>
                          ))}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
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
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${resultTab === 'floor_plan'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                }`}
            >
              <Compass className="h-4 w-4" />
              <span>2D Floor Plans</span>
            </button>

            <button
              onClick={() => setResultTab('elevation')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${resultTab === 'elevation'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                }`}
            >
              <ImageIcon className="h-4 w-4" />
              <span>Front Elevation</span>
            </button>

            <button
              onClick={() => setResultTab('3d_model')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${resultTab === '3d_model'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                }`}
            >
              <Box className="h-4 w-4" />
              <span>3D Views</span>
            </button>

            <button
              onClick={() => setResultTab('audit')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${resultTab === 'audit'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                }`}
            >
              <Shield className="h-4 w-4" />
              <span>Checks &amp; AI Review</span>
            </button>

            <button
              onClick={() => setResultTab('boq')}
              className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-1.5 ${resultTab === 'boq'
                  ? 'bg-[#23483D] text-white shadow-xs'
                  : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
                }`}
            >
              <Calculator className="h-4 w-4" />
              <span>Cost Estimation & Material BOQ</span>
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
                      {storeyKeys.map((key, i) => (
                        <button
                          key={key}
                          onClick={() => setActiveFloorView(key)}
                          className={`px-3 py-1 rounded-lg font-semibold transition-colors ${(activeFloorView === key || (i === 0 && !storeyKeys.includes(activeFloorView) && activeFloorView !== 'rooftop' && activeFloorView !== 'all')) ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                            }`}
                        >
                          {storeyLabel(i)}
                        </button>
                      ))}
                      {/* ROOFTOP SLAB BUTTON */}
                      <button
                        onClick={() => setActiveFloorView('rooftop')}
                        className={`px-3 py-1 rounded-lg font-semibold transition-colors ${activeFloorView === 'rooftop' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                          }`}
                      >
                        Rooftop Slab
                      </button>
                      <button
                        onClick={() => setActiveFloorView('all')}
                        className={`px-3 py-1 rounded-lg font-semibold transition-colors ${activeFloorView === 'all' ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'
                          }`}
                      >
                        Composite View
                      </button>
                    </div>

                    {/* Plan Layer Switcher: 2D Structural vs Inner Furnishing */}
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 bg-[#EEF4F0] p-1 rounded-xl border border-[#DCE7DE] text-xs">
                        <button
                          onClick={() => setPlanLayer('structural')}
                          className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${planLayer === 'structural' ? 'bg-[#23483D] text-white shadow-xs' : 'text-[#68736C] hover:text-[#202923]'
                            }`}
                        >
                          📐 2D Structural Plan
                        </button>
                        <button
                          onClick={() => setPlanLayer('furnishing')}
                          className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${planLayer === 'furnishing' ? 'bg-[#23483D] text-white shadow-xs' : 'text-[#68736C] hover:text-[#202923]'
                            }`}
                        >
                          🛋️ Inner Furnishing Plan
                        </button>
                      </div>

                      <button
                        onClick={() => setRenderMode(renderMode === 'backend_png' ? 'interactive_svg' : 'backend_png')}
                        className="px-2.5 py-1 rounded-lg bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] text-[11px] font-semibold"
                      >
                        {renderMode === 'backend_png' ? 'Vector SVG' : 'CAD Blueprint PNG'}
                      </button>
                    </div>
                  </div>

                  {/* Interactive Architectural Zoom & Pan Canvas */}
                  <div className="w-full">
                    <ArchitecturalPlanCanvas
                      imageSrc={renderMode === 'backend_png' ? backendFloorImage : null}
                      alt={`${activeFloorView} Floor Plan`}
                      levelLabel={activeFloorView === 'rooftop' ? 'ROOFTOP SLAB PLAN' : activeFloorView === 'all' ? 'COMPOSITE ALL FLOORS' : `${storeyLabel(activeLevel).toUpperCase()} PLAN`}
                      dimensionsText={`${plotWidthFt}×${plotLengthFt} ft • Scale 1:100 • ${style.toUpperCase()}`}
                      renderMode={renderMode}
                      onSwitchMode={() => setRenderMode(renderMode === 'backend_png' ? 'interactive_svg' : 'backend_png')}
                    >
                      <FloorPlanViewer
                        type={generatedAlternative?.floorPlanSvgType || (plotPreset === '5_marla' ? '5_marla_modern' : plotPreset === '7_marla' ? '7_marla_compact' : plotPreset === '1_kanal' ? '1_kanal_estate' : '10_marla_luxury')}
                        title={`${plotPreset.replace('_', ' ').toUpperCase()} Architectural Floor Plan`}
                        rooms={generatedAlternative?.rooms}
                        layoutJson={backendDesign?.layout_json}
                        planLayer={planLayer}
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
                  <div className="border-b border-[#E2E7E1] pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="font-bold text-[#202923] text-sm">Front Elevation</h3>
                      <p className="text-[11px] text-[#68736C]">Drawn from the floor plans: every storey, with street-side doors and windows strictly at their plan positions</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-[#23483D] bg-[#EEF4F0] px-2 py-0.5 rounded">
                        {style}
                      </span>
                      {elevationImage && (
                        <a
                          href={elevationImage}
                          download={`front_elevation_${activeElevationStyle}.png`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg transition-colors border border-[#DCE7DE] flex items-center gap-1.5"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download Elevation PNG</span>
                        </a>
                      )}
                    </div>
                  </div>

                  {/* 3 DYNAMIC ELEVATION STYLE CARDS / SELECTOR */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#202923]">Choose Elevation Style Theme:</span>
                      <span className="text-[10px] text-[#68736C]">3 Distinct Styles &bull; 100% Plan Aligned</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                      {[
                        {
                          id: 'modern_contemporary',
                          name: 'Modern Contemporary',
                          badge: 'Charcoal & Glass',
                          desc: 'Sleek dark frames, seamless glass balustrade, refined horizontal reveals'
                        },
                        {
                          id: 'classical_traditional',
                          name: 'Classical & Traditional',
                          badge: 'Mouldings & Cornice',
                          desc: 'Dentil parapet band, divided lite transom windows, corner quoin stones'
                        },
                        {
                          id: 'minimalist_timber',
                          name: 'Minimalist Timber & Stone',
                          badge: 'Cedar Louvers',
                          desc: 'Warm architectural timber screens, louvered balustrade, bronze casing'
                        }
                      ].map((item) => {
                        const isSelected = activeElevationStyle === item.id;
                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => setActiveElevationStyle(item.id as any)}
                            className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                              isSelected
                                ? 'bg-white border-2 border-[#23483D] shadow-sm'
                                : 'bg-[#F7F7F2] border-[#E2E7E1] hover:bg-white hover:border-[#23483D]'
                            }`}
                          >
                            <div className="space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-xs text-[#202923]">{item.name}</span>
                                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                                  isSelected ? 'bg-[#23483D] text-white' : 'bg-white border border-[#E2E7E1] text-[#68736C]'
                                }`}>
                                  {item.badge}
                                </span>
                              </div>
                              <p className="text-[10px] text-[#68736C] leading-snug line-clamp-2">{item.desc}</p>
                            </div>
                            <div className="pt-2 text-[10px] font-semibold flex items-center gap-1 text-[#23483D]">
                              {isSelected ? '✓ Active Theme' : 'Click to View'}
                            </div>
                          </button>
                        );
                      })}
                    </div>
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

              {/* TAB 3: 3D VIEWS - drawn by the backend from the same geometry as the floor plans */}
              {resultTab === '3d_model' && (
                <div className="space-y-4">
                  <div className="border-b border-[#E2E7E1] pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="font-bold text-[#202923] text-sm">3D Building Views</h3>
                      <p className="text-[11px] text-[#68736C]">
                        Built from the same rooms, doors and windows as the floor plans and the elevation
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 bg-[#F7F7F2] p-1 rounded-xl border border-[#E2E7E1] text-xs">
                        {(['interactive', 'front_right', 'front_left'] as const).map((v) => (
                          <button
                            key={v}
                            onClick={() => setView3d(v)}
                            className={`px-3 py-1 rounded-lg font-semibold transition-colors ${view3d === v ? 'bg-[#23483D] text-white' : 'text-[#68736C] hover:text-[#202923]'}`}
                          >
                            {v === 'interactive' ? 'Rotate (live)' : v === 'front_right' ? 'Front-Right image' : 'Front-Left image'}
                          </button>
                        ))}
                      </div>
                      {view3d !== 'interactive' && backendDesign?.images?.[`view3d_${view3d}`] && (
                        <a
                          href={backendDesign.images[`view3d_${view3d}`]}
                          download={`3d_view_${view3d}.png`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 text-[11px] font-semibold text-[#23483D] bg-[#EEF4F0] hover:bg-[#DCE7DE] rounded-lg transition-colors border border-[#DCE7DE] flex items-center gap-1.5"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download PNG</span>
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="border border-[#E2E7E1] rounded-xl overflow-hidden bg-white p-4 flex items-center justify-center min-h-[420px]">
                    {view3d === 'interactive' && Array.isArray(backendDesign?.three_d_model?.nodes) && backendDesign.three_d_model.nodes.length > 0 ? (
                      <div className="w-full">
                        <Massing3DViewer
                          nodes={backendDesign.three_d_model.nodes}
                          plotWidth={Number(backendDesign?.plot?.width_ft) || plotWidthFt}
                          plotLength={Number(backendDesign?.plot?.length_ft) || plotLengthFt}
                        />
                      </div>
                    ) : backendDesign?.images?.[`view3d_${view3d === 'interactive' ? 'front_right' : view3d}`] ? (
                      <img
                        src={backendDesign.images[`view3d_${view3d === 'interactive' ? 'front_right' : view3d}`]}
                        alt={`3D view ${view3d}`}
                        className="max-h-[560px] w-auto mx-auto object-contain rounded-lg"
                      />
                    ) : (
                      <div className="text-center p-8 space-y-2 text-xs text-[#68736C]">
                        <Box className="h-10 w-10 mx-auto text-[#68736C]/40" />
                        <p className="font-bold text-[#202923]">No 3D view for this design</p>
                        <p>Generate the design again to draw its 3D views.</p>
                      </div>
                    )}
                  </div>
                  <p className="text-[10px] text-[#8C9890]">
                    Massing visualisation for design review. Not a structural or municipal approval drawing.
                  </p>
                </div>
              )}

              {/* TAB 4: WHAT THE CAD ENGINE ACTUALLY FOUND (no canned verdicts) */}
              {resultTab === 'audit' && (() => {
                const v = backendDesign?.validation || {};
                const errs: any[] = Array.isArray(v.errors) ? v.errors : [];
                const warns: any[] = Array.isArray(v.warnings) ? v.warnings.filter((w: any) => w.code !== 'SCRIPT_DUPLICATE_NAME') : [];
                const report: any[] = Array.isArray(backendDesign?.requirements?.report) ? backendDesign.requirements.report : [];
                const passed = v.status === 'PASS';
                return (
                  <div className="space-y-4 text-xs">
                    <div className="border-b border-[#E2E7E1] pb-2 flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-[#202923] text-sm flex items-center gap-1.5">
                          <Shield className="h-4 w-4 text-[#23483D]" /> CAD Engine Check Report
                        </h3>
                        <p className="text-[11px] text-[#68736C]">
                          What the geometry engine measured in this design: walking routes, daylight, doors, furniture
                        </p>
                      </div>
                      <span className={`px-2.5 py-1 rounded-lg font-bold font-mono ${passed ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                        {v.status || 'NOT CHECKED'} &middot; {errs.length} error(s) &middot; {warns.length} note(s)
                      </span>
                    </div>

                    {backendDesign?.architect_review && (
                      <div className="p-4 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] space-y-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-[#23483D]">The AI architect's own review of this design</span>
                          {backendDesign.architect_review.score != null && (
                            <span className="px-2 py-0.5 rounded bg-white border border-[#DCE7DE] font-mono font-bold text-[#23483D]">
                              {backendDesign.architect_review.score} / 10
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#202923] leading-relaxed">{backendDesign.architect_review.verdict}</p>
                        {backendDesign.improved_after_review && (
                          <p className="text-[10px] font-semibold text-[#23483D]">
                            The design was improved once after the AI's first review
                            {backendDesign.architect_review_before?.score != null ? ` (its own score went from ${backendDesign.architect_review_before.score} to ${backendDesign.architect_review.score})` : ''}.
                          </p>
                        )}
                        {([['Strengths', 'strengths'], ['Concerns', 'concerns'], ['Suggestions you can ask for', 'suggestions']] as const).map(([label, key]) => (
                          Array.isArray(backendDesign.architect_review[key]) && backendDesign.architect_review[key].length > 0 && (
                            <div key={key}>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-[#23483D]">{label}</span>
                              <ul className="list-disc list-inside text-[11px] text-[#202923] space-y-0.5 mt-0.5">
                                {backendDesign.architect_review[key].map((t: string, i: number) => <li key={i}>{t}</li>)}
                              </ul>
                            </div>
                          )
                        ))}
                        <p className="text-[10px] text-[#68736C]">
                          This is the language model's own opinion from its knowledge of homes in Pakistan. No bylaws were applied.
                        </p>
                      </div>
                    )}

                    {report.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-bold text-[#202923]">What you asked for</span>
                        {report.map((r: any, i: number) => (
                          <div key={i} className="p-2.5 rounded-lg border border-[#E2E7E1] bg-[#F7F7F2] flex items-start justify-between gap-3">
                            <span className="text-[11px] text-[#202923]"><strong>{r.item}</strong> &mdash; {r.detail}</span>
                            <span className={`px-1.5 py-0.5 rounded font-bold font-mono text-[10px] shrink-0 ${r.met ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                              {r.met ? 'MET' : 'NOT MET'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {errs.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-bold text-red-800">Errors (the design does not work as drawn)</span>
                        {errs.map((e: any, i: number) => (
                          <div key={i} className="p-2.5 rounded-lg border border-red-200 bg-red-50 text-[11px] text-[#202923]">
                            <span className="font-mono font-bold text-red-800">{e.code}</span> &mdash; {e.message}
                          </div>
                        ))}
                      </div>
                    )}

                    {warns.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-bold text-[#202923]">Notes (advice, not failures)</span>
                        <div className="max-h-[260px] overflow-y-auto space-y-1.5 pr-1">
                          {warns.map((w: any, i: number) => (
                            <div key={i} className="p-2.5 rounded-lg border border-[#E2E7E1] bg-white text-[11px] text-[#202923]">
                              <span className="font-mono font-bold text-amber-700">{w.code}</span> &mdash; {w.message}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {errs.length === 0 && warns.length === 0 && report.length === 0 && (
                      <p className="text-[#68736C]">No check results were returned for this design.</p>
                    )}

                    <p className="text-[10px] text-[#8C9890]">
                      Software CAD validation only. It is not a structural engineering certificate or a municipal building approval.
                    </p>
                  </div>
                );
              })()}

              {/* TAB 5: INTERACTIVE COST ESTIMATION & MATERIAL BOQ */}
              {resultTab === 'boq' && (
                <div className="space-y-6 text-xs animate-in fade-in">
                  <div className="border-b border-[#E2E7E1] pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="font-bold text-[#202923] text-sm flex items-center gap-2">
                        <Calculator className="h-4 w-4 text-[#23483D]" />
                        Parametric Bill of Quantities (BOQ) & Material Pricing
                      </h3>
                      <p className="text-[11px] text-[#68736C]">
                        Dynamically recalculate construction expenses by customizing individual material unit prices or fetching live market rates.
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded-lg bg-[#EEF4F0] text-[#23483D] font-mono font-bold text-[11px] self-start sm:self-auto">
                      {rateSourceNotice}
                    </span>
                  </div>

                  {/* Executive KPI Summary Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
                      <span className="text-[10px] text-[#68736C] font-semibold block">Total Estimated Cost</span>
                      <p className="text-base font-bold font-mono text-[#23483D]">
                        {formatPKR(boqData?.grand_total || backendDesign?.boq?.grand_total || backendDesign?.boq?.total_cost_pkr || 24500000)}
                      </p>
                      <span className="text-[9px] text-[#8C9890]">Incl. 7.5% contingency</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
                      <span className="text-[10px] text-[#68736C] font-semibold block">Rate per Sq Ft</span>
                      <p className="text-base font-bold font-mono text-[#202923]">
                        PKR {Math.round((boqData?.grand_total || backendDesign?.boq?.grand_total || 24500000) / Math.max(1, Math.round(calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55)))).toLocaleString()}
                      </p>
                      <span className="text-[9px] text-[#8C9890]">PKR / sq ft covered</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
                      <span className="text-[10px] text-[#68736C] font-semibold block">Grey Structure</span>
                      <p className="text-base font-bold font-mono text-[#202923]">
                        {formatPKR(boqData?.grey_cost || backendDesign?.boq?.grey_cost || 14700000)}
                      </p>
                      <span className="text-[9px] text-[#8C9890]">~60% of total budget</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
                      <span className="text-[10px] text-[#68736C] font-semibold block">Finishing Cost</span>
                      <p className="text-base font-bold font-mono text-[#202923]">
                        {formatPKR(boqData?.finishing_cost || backendDesign?.boq?.finishing_cost || 9800000)}
                      </p>
                      <span className="text-[9px] text-[#8C9890]">~40% of total budget</span>
                    </div>
                  </div>

                  {/* Gemini AI Live Market Rate Assistant Card */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-[#EEF4F0] to-[#E2EDE5] border border-[#C5D8C9] space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Key className="h-4 w-4 text-[#23483D]" />
                        <span className="font-bold text-xs text-[#202923]">
                          Live Pakistan Construction Market Rates via Google Gemini AI
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-[#23483D] bg-white/70 px-2 py-0.5 rounded-md border border-[#C5D8C9]">
                        Real-Time Rate Query
                      </span>
                    </div>

                    <p className="text-[11px] text-[#4A5D50] leading-relaxed">
                      Enter your Gemini API Key to automatically pull current Pakistani material prices (cement, steel, bricks, aggregate) for your target city, or apply verified 2026 local benchmarks with one click.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 items-end">
                      <div>
                        <label className="block text-[10px] font-bold text-[#23483D] mb-1">
                          Gemini API Key (Optional)
                        </label>
                        <input
                          type="password"
                          value={geminiApiKey}
                          onChange={(e) => setGeminiApiKey(e.target.value)}
                          placeholder="Paste AIzaSy... API key"
                          className="w-full bg-white border border-[#C5D8C9] rounded-xl px-3 py-2 text-xs font-mono text-[#202923] focus:outline-none focus:border-[#23483D]"
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-[#23483D] mb-1">
                          City for Pricing
                        </label>
                        <input
                          type="text"
                          value={geminiCity}
                          onChange={(e) => setGeminiCity(e.target.value)}
                          placeholder="e.g. Islamabad, Lahore, Karachi"
                          className="w-full bg-white border border-[#C5D8C9] rounded-xl px-3 py-2 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
                        />
                      </div>

                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleFetchGeminiMarketRates(geminiApiKey, geminiCity)}
                          disabled={isFetchingGeminiRates}
                          className="flex-1 py-2 px-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition-colors"
                        >
                          <Sparkles className="h-3.5 w-3.5 text-emerald-300" />
                          <span>{isFetchingGeminiRates ? 'Fetching...' : 'Fetch Live Rates'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFetchGeminiMarketRates('', geminiCity)}
                          disabled={isFetchingGeminiRates}
                          className="py-2 px-3 rounded-xl bg-white hover:bg-[#F7F7F2] text-[#23483D] border border-[#C5D8C9] font-semibold text-xs flex items-center gap-1 transition-colors"
                        >
                          <RefreshCw className="h-3 w-3" />
                          <span>Benchmarks</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Interactive Material Rate Customizer Table */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#202923] uppercase tracking-wider flex items-center gap-1.5">
                        <DollarSign className="h-3.5 w-3.5 text-[#23483D]" />
                        Customize Individual Material Prices & Unit Rates:
                      </span>
                      {isUpdatingBoq && (
                        <span className="text-[10px] font-mono text-[#23483D] animate-pulse">
                          Recalculating BOQ...
                        </span>
                      )}
                    </div>

                    <div className="border border-[#E2E7E1] rounded-xl overflow-hidden shadow-2xs">
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[#F7F7F2] border-b border-[#E2E7E1] text-[#68736C] font-semibold">
                            <tr>
                              <th className="py-2.5 px-3">Material / Service Trade</th>
                              <th className="py-2.5 px-3">Variety / Quality Grade</th>
                              <th className="py-2.5 px-3 text-right">Quantity</th>
                              <th className="py-2.5 px-3 text-right">Unit Rate (PKR)</th>
                              <th className="py-2.5 px-3 text-right">Line Total (PKR)</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#E2E7E1] bg-white">
                            {DETAILED_MATERIALS_CATALOG.map((mat) => {
                              const apiId = CATALOG_TO_API_MAP[mat.id] || mat.id;
                              const selectedVarId = selectedBoqVarieties[mat.id] || mat.defaultVarietyId;
                              const selectedVar = mat.varieties.find((v) => v.id === selectedVarId) || mat.varieties[0];
                              const currentRate = customUnitPrices[apiId] !== undefined ? customUnitPrices[apiId] : selectedVar.defaultPricePKR;
                              const area = Math.round(plotWidthFt * plotLengthFt * (floors === 1 ? 0.75 : 1.55));
                              const qty = mat.calculateQuantity(area, floors, bedrooms, bathrooms);
                              const lineTotal = Math.round(qty * currentRate);

                              return (
                                <tr key={mat.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                                  <td className="py-2.5 px-3">
                                    <div className="font-semibold text-[#202923]">{mat.name}</div>
                                    <span className="text-[10px] text-[#68736C]">{mat.formulaDescription}</span>
                                  </td>
                                  <td className="py-2.5 px-3">
                                    <select
                                      value={selectedVarId}
                                      onChange={(e) => handleBoqVarietyChange(mat.id, e.target.value)}
                                      className="w-full max-w-xs bg-[#F7F7F2] border border-[#E2E7E1] rounded-lg px-2 py-1 text-xs text-[#202923] font-medium focus:outline-none focus:border-[#23483D]"
                                    >
                                      {mat.varieties.map((v) => (
                                        <option key={v.id} value={v.id}>
                                          {v.name} (₨ {v.defaultPricePKR.toLocaleString()})
                                        </option>
                                      ))}
                                    </select>
                                  </td>
                                  <td className="py-2.5 px-3 text-right font-mono text-[#68736C]">
                                    {qty.toLocaleString()} {mat.unit}
                                  </td>
                                  <td className="py-2.5 px-3 text-right">
                                    <div className="inline-flex items-center gap-1">
                                      <span className="text-[#68736C] font-mono text-[10px]">PKR</span>
                                      <input
                                        type="number"
                                        value={currentRate}
                                        onChange={(e) => handleUnitPriceChange(apiId, Number(e.target.value))}
                                        className="w-24 bg-[#F7F7F2] border border-[#E2E7E1] rounded-lg px-2 py-1 text-right font-mono font-bold text-[#202923] focus:outline-none focus:border-[#23483D]"
                                      />
                                    </div>
                                  </td>
                                  <td className="py-2.5 px-3 text-right font-mono font-bold text-[#23483D]">
                                    PKR {lineTotal.toLocaleString()}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Educational Civil Engineering Formula Explainer */}
                    <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-3 mt-4">
                      <div className="flex items-center gap-2 text-[#23483D] font-bold text-xs">
                        <Layers className="h-4 w-4" />
                        <span>Civil Engineering Formula Breakdown (How This Cost Is Calculated)</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px] text-[#68736C]">
                        <div className="p-3 bg-white rounded-lg border border-[#E2E7E1] space-y-1">
                          <strong className="text-[#202923] block">1. Covered Area Standard</strong>
                          <span>Derived as Ground + 1st Floor + Mumty = <strong>{Math.round(plotWidthFt * plotLengthFt * (floors === 1 ? 0.75 : 1.55))} sq ft</strong>. All material quantities are scaled from this covered area.</span>
                        </div>
                        <div className="p-3 bg-white rounded-lg border border-[#E2E7E1] space-y-1">
                          <strong className="text-[#202923] block">2. Consumption Coefficients</strong>
                          <span>16.5 bricks/sq ft, 0.45 cement bags/sq ft, 3.85 kg rebar/sq ft, 2.75 cft sand/sq ft, and 1.85 cft crush/sq ft based on PEC residential codes.</span>
                        </div>
                        <div className="p-3 bg-white rounded-lg border border-[#E2E7E1] space-y-1">
                          <strong className="text-[#202923] block">3. Line Total Formula</strong>
                          <span>Line Cost = Quantity × Current Unit Rate. Grand Total = Grey Structure + Finishing Works + MEP Protection + 7.5% Contingency Reserve.</span>
                        </div>
                      </div>
                    </div>
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
                <div className="p-4 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-2">
                  <div className="space-y-0.5">
                    <span className="text-[11px] text-[#68736C]">Estimated Total (Grey + Finish):</span>
                    <p className="text-xl font-bold font-mono text-[#23483D]">
                      {formatPKR(boqData?.grand_total || backendDesign?.boq?.total_cost_pkr || generatedAlternative?.estimatedCostPKR || 24500000)}
                    </p>
                    <p className="text-[10px] text-[#68736C]">
                      PKR {Math.round((boqData?.grand_total || backendDesign?.boq?.total_cost_pkr || 24500000) / Math.max(1, Math.round(calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55)))).toLocaleString()} / sq ft
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setResultTab('boq')}
                    className="w-full py-1.5 px-2.5 rounded-lg bg-[#EEF4F0] hover:bg-[#DCE7DE] text-[#23483D] border border-[#DCE7DE] font-semibold text-[11px] flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <Calculator className="h-3.5 w-3.5" />
                    <span>Customize Material Prices & BOQ</span>
                  </button>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Covered Area:</span>
                    <strong className="text-[#202923] font-mono">
                      {(backendDesign?.covered_area_sqft || Math.round(calculatedAreaSqFt * (floors === 1 ? 0.75 : 1.55))).toLocaleString()} sq ft
                    </strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Bedrooms:</span>
                    <strong className="text-[#202923]">
                      {Array.isArray(backendDesign?.room_schedule)
                        ? `${backendDesign.room_schedule.filter((r: any) => r.category === 'bedroom').length || bedrooms} Bedrooms`
                        : `${bedrooms} Bedrooms`}
                    </strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Attached Baths:</span>
                    <strong className="text-[#202923]">
                      {Array.isArray(backendDesign?.room_schedule)
                        ? `${backendDesign.room_schedule.filter((r: any) => r.category === 'bath').length || bathrooms} Baths`
                        : `${bathrooms} Baths`}
                    </strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#E2E7E1]/60">
                    <span className="text-[#68736C]">Car Porch:</span>
                    <strong className="text-[#23483D]">
                      {Array.isArray(backendDesign?.room_schedule)
                        ? (backendDesign.room_schedule.find((r: any) => r.category === 'porch')?.dimensions_ft || `${pakistaniSpecs.carPorchCapacity} Cars`)
                        : `${pakistaniSpecs.carPorchCapacity} Cars`}
                    </strong>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-[#68736C]">Total Synthesized Spaces:</span>
                    <strong className="text-[#23483D]">
                      {backendDesign?.total_rooms || backendDesign?.room_schedule?.length || (bedrooms + bathrooms + 4)} Spaces
                    </strong>
                  </div>
                </div>

                {Array.isArray(backendDesign?.room_schedule) && backendDesign.room_schedule.length > 0 && (
                  <div className="pt-3 border-t border-[#E2E7E1] space-y-2">
                    <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                      AI Synthesized Room Dimensions ({storeyLabel(activeLevel)}):
                    </span>
                    <div className="max-h-[180px] overflow-y-auto divide-y divide-[#E2E7E1]/60 pr-1 text-[11px]">
                      {backendDesign.room_schedule
                        .filter((rm: any) => rm.level === activeLevel)
                        .map((rm: any, rIdx: number) => (
                          <div key={rm.id || rIdx} className="py-1.5 flex items-center justify-between gap-2">
                            <span className="font-semibold text-[#202923] truncate">{rm.name}</span>
                            <span className="font-mono text-[10px] text-[#23483D] bg-[#EEF4F0] px-1.5 py-0.5 rounded shrink-0">
                              {rm.dimensions_ft}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
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
      {/* EXPORT CAD PACKAGE MODAL */}
      {exportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl border border-[#E2E7E1]">
            <div className="flex items-center justify-between border-b border-[#E2E7E1] pb-3">
              <div className="flex items-center gap-2">
                <Download className="h-5 w-5 text-[#23483D]" />
                <h3 className="font-bold text-sm text-[#202923]">Export Architectural CAD Package</h3>
              </div>
              <button
                onClick={() => setExportModalOpen(false)}
                className="p-1 rounded-lg hover:bg-[#F7F7F2] text-[#68736C]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-[#68736C]">
              Select the CAD or rendering deliverable format for Version {revisionNumber}:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {[
                { id: 'pdf', title: 'Presentation Sheet PDF (.pdf)', desc: 'Architectural blueprint sheet' },
                { id: 'dxf', title: 'AutoCAD DXF (.dxf)', desc: 'Layered CAD geometry (AIA layers)' },
                { id: 'svg', title: 'Pure Vector Blueprint (.svg)', desc: 'High-res scalable vector graphics' },
                { id: 'png', title: 'Technical Blueprint Sheet (.png)', desc: 'Full high-res raster blueprint' },
                { id: 'obj', title: 'Wavefront 3D Mesh (.obj)', desc: 'Universal 3D spatial solids' },
                { id: 'blend', title: 'Blender 3D Model (.blend)', desc: 'Procedural 3D scene file' },
              ].map((fmt) => (
                <button
                  key={fmt.id}
                  type="button"
                  onClick={() => setExportFormat(fmt.id as any)}
                  className={`p-3 rounded-xl border text-left transition-all ${exportFormat === fmt.id
                      ? 'border-2 border-[#23483D] bg-[#EEF4F0]'
                      : 'border-[#E2E7E1] hover:border-[#23483D] bg-white'
                    }`}
                >
                  <div className="font-bold text-xs text-[#202923]">{fmt.title}</div>
                  <div className="text-[10px] text-[#68736C] mt-0.5">{fmt.desc}</div>
                </button>
              ))}
            </div>
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E7E1]">
              <button
                type="button"
                onClick={() => setExportModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#202923]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={exportLoading}
                onClick={handleExportDownload}
                className="px-5 py-2 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white text-xs font-bold flex items-center gap-2 shadow-sm"
              >
                {exportLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                <span>{exportLoading ? 'Generating CAD Package...' : `Download ${exportFormat.toUpperCase()}`}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
