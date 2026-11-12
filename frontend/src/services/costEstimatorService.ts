import { CostEstimate, CostBreakdown } from '../types';

export interface MaterialVarietyOption {
  id: string;
  name: string;
  description: string;
  defaultPricePKR: number;
  unit: string;
}

export interface DetailedMaterialDefinition {
  id: string;
  name: string;
  category: 'grey' | 'finishing' | 'mep_labor';
  categoryLabel: string;
  unit: string;
  formulaDescription: string;
  civilEngineeringNotes: string;
  varieties: MaterialVarietyOption[];
  defaultVarietyId: string;
  calculateQuantity: (coveredArea: number, floors: number, beds: number, baths: number) => number;
}

export const DETAILED_MATERIALS_CATALOG: DetailedMaterialDefinition[] = [
  {
    id: 'bricks',
    name: 'Burnt Red Clay Bricks / Solid Blocks',
    category: 'grey',
    categoryLabel: 'Grey Structure (Masonry)',
    unit: 'bricks',
    formulaDescription: 'Covered Area (sq ft) × 16.5 bricks',
    civilEngineeringNotes: 'Calculated for 9" external load-bearing & boundary walls, 4.5" interior partitions, foundation footing steps, and 3 ft rooftop parapet wall.',
    defaultVarietyId: 'awwal_kiln',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 16.5),
    varieties: [
      { id: 'awwal_kiln', name: 'Awwal Kiln Burnt Clay Red Bricks (Grade 1)', description: 'Standard high-strength burnt clay brick with sharp edges and uniform red color.', defaultPricePKR: 14.50, unit: 'per brick' },
      { id: 'doem_kiln', name: 'Doem Kiln Bricks (Grade 2)', description: 'Slightly lower strength brick for foundation filling and non-load-bearing walls.', defaultPricePKR: 12.00, unit: 'per brick' },
      { id: 'concrete_block', name: 'Solid Concrete Blocks (8"×8"×16")', description: 'Vibrated hollow/solid concrete masonry blocks, faster construction with less mortar.', defaultPricePKR: 85.00, unit: 'per block' },
      { id: 'aac_block', name: 'Autoclaved Aerated Concrete (AAC) Blocks', description: 'Ultra-lightweight thermal insulating blocks, reduces building dead load by 50%.', defaultPricePKR: 115.00, unit: 'per block' },
    ],
  },
  {
    id: 'cement',
    name: 'Portland Cement (50kg Bags)',
    category: 'grey',
    categoryLabel: 'Grey Structure (Concrete & Mortar)',
    unit: 'bags',
    formulaDescription: 'Covered Area (sq ft) × 0.45 bags',
    civilEngineeringNotes: '0.22 bags/sq ft for 1:2:4 RCC slabs/beams/columns, 0.13 bags/sq ft for 1:6 brick mortar, and 0.10 bags/sq ft for internal/external double plaster.',
    defaultVarietyId: 'opc_fauji_bestway',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 0.45),
    varieties: [
      { id: 'opc_fauji_bestway', name: 'Ordinary Portland Cement OPC Grade 53 (Bestway / Fauji / Lucky)', description: 'Premium 53 Grade cement for high-stress RCC slabs, columns, and plinth beams.', defaultPricePKR: 1450, unit: 'per 50kg bag' },
      { id: 'src_sulphate', name: 'Sulphate Resistant Cement SRC (Foundation & Tank)', description: 'Prevents chemical salt attack in underground foundations, basement walls, and water reservoirs.', defaultPricePKR: 1550, unit: 'per 50kg bag' },
      { id: 'composite_cement', name: 'Portland Composite Cement PCC (General Mortar)', description: 'Low heat of hydration, optimal for brickwork and plastering.', defaultPricePKR: 1380, unit: 'per 50kg bag' },
      { id: 'white_cement', name: 'White Cement (Maple Leaf / Decorative)', description: 'High-purity white cement used for tile grouting and decorative terrazzo.', defaultPricePKR: 2400, unit: 'per 50kg bag' },
    ],
  },
  {
    id: 'steel',
    name: 'Grade-60 Deformed Steel Rebar',
    category: 'grey',
    categoryLabel: 'Grey Structure (Structural Steel)',
    unit: 'tons',
    formulaDescription: 'Covered Area (sq ft) × 0.00385 tons (3.85 kg / sq ft)',
    civilEngineeringNotes: 'Structural engineering code requirement for Seismic Zone 2B: 6" two-way RCC suspended slabs, concealed/drop beams, tied columns, and underground water reservoir.',
    defaultVarietyId: 'grade60_prime',
    calculateQuantity: (area, floors, beds, baths) => parseFloat((area * 0.00385).toFixed(2)),
    varieties: [
      { id: 'grade60_prime', name: 'Prime Grade-60 Billet Rebar ASTM A615 (Amreli / Mughal / Mughal Supreme)', description: '100% prime billet steel with 60,000 PSI guaranteed yield strength and certified earthquake ductility.', defaultPricePKR: 275000, unit: 'per metric ton' },
      { id: 'grade60_commercial', name: 'Grade-60 Rerolled Steel (Commercial)', description: 'Standard rerolled steel from ship-breaking plates, suitable for low-rise residential.', defaultPricePKR: 255000, unit: 'per metric ton' },
      { id: 'grade40_mild', name: 'Grade-40 Mild Steel (Stirrups & Ties)', description: 'Flexible mild steel used primarily for column rings and beam stirrups.', defaultPricePKR: 245000, unit: 'per metric ton' },
      { id: 'prefab_cut_bend', name: 'Pre-Engineered Cut & Bend Steel with Stirrups', description: 'Factory-cut and machine-bent rebar, eliminates site cutting wastage and reduces labor time.', defaultPricePKR: 290000, unit: 'per metric ton' },
    ],
  },
  {
    id: 'sand',
    name: 'Coarse & Fine River Sand',
    category: 'grey',
    categoryLabel: 'Grey Structure (Aggregates)',
    unit: 'cft',
    formulaDescription: 'Covered Area (sq ft) × 2.75 cft',
    civilEngineeringNotes: '1.40 cft coarse sand for concrete batching (1:2:4 ratio) + 0.85 cft for brick masonry mortar + 0.50 cft for wall plaster.',
    defaultVarietyId: 'chenab_sand',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 2.75),
    varieties: [
      { id: 'chenab_sand', name: 'Chenab River Coarse Sharp Sand (Screened)', description: 'Coarse angular particles ideal for high-strength RCC slabs, columns, and structural casting.', defaultPricePKR: 52, unit: 'per cft' },
      { id: 'ravi_sand', name: 'Ravi River Fine Washed Sand (Plastering)', description: 'Fine grain silt-free sand for smooth internal wall plaster and brick joint mortar.', defaultPricePKR: 38, unit: 'per cft' },
      { id: 'lawrencepur_sand', name: 'Lawrencepur Pit Coarse Washed Sand', description: 'Premium washed pit sand favored in Islamabad/Rawalpindi for superior concrete bonding.', defaultPricePKR: 75, unit: 'per cft' },
      { id: 'bolhari_sand', name: 'Bolhari River Coarse Sand (Sindh)', description: 'Standard sharp sand utilized in Karachi and Lower Sindh construction.', defaultPricePKR: 45, unit: 'per cft' },
    ],
  },
  {
    id: 'crush',
    name: 'Margalla / Sargodha Coarse Aggregate (Crush)',
    category: 'grey',
    categoryLabel: 'Grey Structure (Aggregates)',
    unit: 'cft',
    formulaDescription: 'Covered Area (sq ft) × 1.85 cft',
    civilEngineeringNotes: 'Batching ratio 1:2:4 requires double the aggregate volume of cement. Slabs, beams, and columns consume 1.85 cft graded blue stone per sq ft.',
    defaultVarietyId: 'margalla_crush',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 1.85),
    varieties: [
      { id: 'margalla_crush', name: 'Margalla Blue Limestone Graded Stone (1/2" & 3/4")', description: 'Hard crystalline blue limestone from Margalla Hills, top compressive strength for RCC.', defaultPricePKR: 135, unit: 'per cft' },
      { id: 'sargodha_crush', name: 'Sargodha Black Stone Crush (1/2" & 3/4")', description: 'Dense igneous black quarry stone, standard choice across Punjab.', defaultPricePKR: 110, unit: 'per cft' },
      { id: 'dina_crush', name: 'Dina / Mangla River Gravel Crush', description: 'Screened crushed river shingles, economical for foundation footings and ground flooring.', defaultPricePKR: 95, unit: 'per cft' },
      { id: 'subbase_ballast', name: 'Stone Ballast & Soling Stone (Sub-base)', description: 'Larger coarse stone for foundation base compaction and floor plinth packing.', defaultPricePKR: 75, unit: 'per cft' },
    ],
  },
  {
    id: 'civil_labor',
    name: 'Civil Construction Labor & Shuttering',
    category: 'grey',
    categoryLabel: 'Grey Structure (Labor & Formwork)',
    unit: 'sq ft',
    formulaDescription: 'Covered Area (sq ft) × 1.0 sq ft',
    civilEngineeringNotes: 'Includes master masons (rajgir), steel fixers, concrete pourers, mechanical vibrator rental, scaffolding, and steel formwork shuttering.',
    defaultVarietyId: 'grey_labor_steel',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area),
    varieties: [
      { id: 'grey_labor_steel', name: 'Grey Structure Labor with Steel Shuttering & Vibrator Rig', description: 'Full mechanized shuttering with steel sheets, props, mixer machine, and vibration consolidation.', defaultPricePKR: 480, unit: 'per sq ft covered' },
      { id: 'grey_labor_wood', name: 'Grey Structure Labor with Wooden Formwork', description: 'Traditional timber formwork shuttering, economical but requires careful leveling.', defaultPricePKR: 420, unit: 'per sq ft covered' },
      { id: 'finishing_labor_rate', name: 'Finishing Works Labor (Tiles, Paint, Polish)', description: 'Specialist tradesmen for tile fixing, marble grinding, false ceilings, and painting.', defaultPricePKR: 380, unit: 'per sq ft covered' },
      { id: 'turnkey_labor_rate', name: 'Turnkey Master Contractor Labor (Grey + Finishing)', description: 'End-to-end full contractor supervision and all specialized labor under single warranty.', defaultPricePKR: 820, unit: 'per sq ft covered' },
    ],
  },
  {
    id: 'tiles',
    name: 'Flooring, Porcelain Tiles & Marbles',
    category: 'finishing',
    categoryLabel: 'Finishing Works (Surfaces)',
    unit: 'sq ft',
    formulaDescription: 'Covered Area (sq ft) × 0.85 sq ft (Includes 12% cutting wastage)',
    civilEngineeringNotes: 'Net carpet flooring area (~72% of covered area) + bathroom wall dado tiles up to 7 ft + 4" perimeter skirting + 12% diagonal cutting margin.',
    defaultVarietyId: 'porcelain_large',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 0.85),
    varieties: [
      { id: 'porcelain_large', name: 'Glazed Porcelain Tiles 24"×48" (Master / Stile / Imported)', description: 'Large format rectified porcelain with high stain resistance and mirror nano-polish.', defaultPricePKR: 380, unit: 'per sq ft' },
      { id: 'porcelain_medium', name: 'Double Body Vitrified Tiles 24"×24"', description: 'Durable full-body vitrified porcelain tiles for high-traffic lounge and bedroom areas.', defaultPricePKR: 280, unit: 'per sq ft' },
      { id: 'ceramic_tiles', name: 'Standard Ceramic Glazed Floor & Wall Tiles', description: 'Economical ceramic tiles for bathroom walls and utility/servant areas.', defaultPricePKR: 190, unit: 'per sq ft' },
      { id: 'marble_sunny_grey', name: 'Sunny Grey / Badal Pakistan Marble (Polished)', description: 'Natural Pakistani marble slabs with crystalline polish, ideal for stair treads and corridors.', defaultPricePKR: 220, unit: 'per sq ft' },
      { id: 'granite_imported', name: 'Imported Black Galaxy / Pearl Granite', description: 'Heavy-duty natural granite for kitchen countertops, island cooking bays, and thresholds.', defaultPricePKR: 650, unit: 'per sq ft' },
    ],
  },
  {
    id: 'paint',
    name: 'Interior Paint, Exterior Weather-Shield & Putty',
    category: 'finishing',
    categoryLabel: 'Finishing Works (Surfaces)',
    unit: 'sq ft',
    formulaDescription: 'Covered Area (sq ft) × 3.40 sq ft (Total Surface Multiplier)',
    civilEngineeringNotes: 'Total surface area covers internal walls (both sides), ceilings, staircase soffits, boundary walls, and exterior facade (3.4× floor area).',
    defaultVarietyId: 'dulux_luxury_emulsion',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area * 3.4),
    varieties: [
      { id: 'dulux_luxury_emulsion', name: 'Dulux Velvet Touch Plastic Emulsion + Weathershield Ultra', description: 'Triple coat acrylic putty with luxury sheen washable emulsion and 7-year silicone exterior shield.', defaultPricePKR: 65, unit: 'per sq ft surface' },
      { id: 'berger_silk_emulsion', name: 'Berger Elegance Silk Emulsion + Weathercoat', description: 'Smooth silk finish with anti-fungal formulation and durable exterior barrier.', defaultPricePKR: 54, unit: 'per sq ft surface' },
      { id: 'brighto_allplast', name: 'Brighto All-Plast Interior + Weather-Proof', description: 'Proven Pakistani formulation with acrylic wall putty base.', defaultPricePKR: 45, unit: 'per sq ft surface' },
      { id: 'distemper_economy', name: 'Standard Distemper with Chalk Putty Base', description: 'Budget chalk-based coating suitable for rental or economical constructions.', defaultPricePKR: 30, unit: 'per sq ft surface' },
    ],
  },
  {
    id: 'doors',
    name: 'Doors, Woodwork & Security Locks',
    category: 'finishing',
    categoryLabel: 'Finishing Works (Carpentry & Openings)',
    unit: 'sets',
    formulaDescription: 'Bedrooms + Bathrooms + 4 (Main, Lounge, Kitchen, Mumty)',
    civilEngineeringNotes: 'Includes main entrance double door, drawing room double-leaf, bedroom suites, bathroom doors, kitchen fire door, and rooftop mumty weather door.',
    defaultVarietyId: 'semi_solid_interior',
    calculateQuantity: (area, floors, beds, baths) => beds + baths + 4,
    varieties: [
      { id: 'solid_ashwood_main', name: 'Solid Ashwood / Teak Main Door + Italian Mortise Lock', description: 'Handcrafted seasoned solid ashwood entrance door (8ft height) with heavy-duty security hardware.', defaultPricePKR: 75000, unit: 'per door set' },
      { id: 'semi_solid_interior', name: 'Semi-Solid Ashwood Veneer Bedroom Doors (1.5" Thick)', description: 'Engineered solid core with natural wood veneer skin and brass cylindrical locks.', defaultPricePKR: 32000, unit: 'per door set' },
      { id: 'pvc_waterproof_bath', name: '100% Waterproof Heavy Fiber PVC Bathroom Doors', description: 'Zero swelling, moisture-resistant bathroom doors with aluminum framing and stainless hinges.', defaultPricePKR: 18000, unit: 'per door set' },
      { id: 'flush_door_commercial', name: 'Commercial Flush Core Laminated Doors', description: 'Lightweight honeycomb or chipboard core with laminated wood-grain finish.', defaultPricePKR: 22000, unit: 'per door set' },
    ],
  },
  {
    id: 'windows',
    name: 'Windows, Glazing & Skylights',
    category: 'finishing',
    categoryLabel: 'Finishing Works (Carpentry & Openings)',
    unit: 'units',
    formulaDescription: 'Bedrooms × 2 + 4 (Lounge, Kitchen, Drawing Room, Stairwell)',
    civilEngineeringNotes: 'Covers front elevation panoramic window bays, bedroom sliding sashes, kitchen exhaust casements, and OTS lightwell ventilation shafts.',
    defaultVarietyId: 'aluminum_16mm',
    calculateQuantity: (area, floors, beds, baths) => beds * 2 + 4,
    varieties: [
      { id: 'aluminum_16mm', name: 'Powder-Coated Aluminum Windows 1.6mm with 5mm Tinted Glass', description: 'Standard high-grade architectural section with insect screens and EPDM weather seals.', defaultPricePKR: 28000, unit: 'per window unit' },
      { id: 'upvc_double_glazed', name: 'German UPVC Double Glazed 24mm (Sound & Thermal Proof)', description: 'Multi-chambered UPVC profiles with argon gas filled double glazing for 40% energy savings.', defaultPricePKR: 44000, unit: 'per window unit' },
      { id: 'thermal_break_aluminum', name: 'Premium Thermal-Break Aluminum Section with Low-E Glass', description: 'Architectural luxury thermal break section preventing heat transmission.', defaultPricePKR: 68000, unit: 'per window unit' },
      { id: 'aluminum_12mm_economy', name: 'Economy Aluminum Windows 1.2mm Section', description: 'Lightweight residential aluminum section with clear 5mm glass.', defaultPricePKR: 19000, unit: 'per window unit' },
    ],
  },
  {
    id: 'sanitary',
    name: 'Plumbing, Piping & Sanitary Fixtures',
    category: 'finishing',
    categoryLabel: 'Finishing Works (MEP Sanitary)',
    unit: 'bath sets',
    formulaDescription: '1 Complete Set per Attached Bathroom',
    civilEngineeringNotes: 'Includes wall-hung or floor-mounted commode, vanity basin, shower mixer set, muslim shower, gully trap, and PPRC water loop connection.',
    defaultVarietyId: 'standard_ceramic_master',
    calculateQuantity: (area, floors, beds, baths) => baths,
    varieties: [
      { id: 'porta_luxury_wallhung', name: 'Porta / Grohe Luxury Wall-Hung Commode + Concealed Cistern & Brass Mixers', description: 'Concealed tank wall-hung porcelain commode with imported single-lever brass chrome mixers.', defaultPricePKR: 75000, unit: 'per bathroom set' },
      { id: 'standard_ceramic_master', name: 'Master / IIL Standard One-Piece Commode + Vanity Basin + Chrome Mixers', description: 'High-quality Pakistani ceramic one-piece commode with granite vanity basin and quarter-turn taps.', defaultPricePKR: 45000, unit: 'per bathroom set' },
      { id: 'economy_sanitary_set', name: 'Economy Ceramic Two-Piece Commode + Basin + Local Mixers', description: 'Standard floor-mounted sanitary ware with local brass chrome fittings.', defaultPricePKR: 26000, unit: 'per bathroom set' },
      { id: 'pprc_pvc_piping', name: 'Heavy Gauge PPRC Water Supply Loops + PVC Sewerage Stacks', description: 'Popular / Master PN20 hot/cold water pipes and 4" Class-B drainage lines.', defaultPricePKR: 35000, unit: 'per bathroom set' },
    ],
  },
  {
    id: 'electrical',
    name: 'Electrical Wiring, Conduits & Smart LED Lighting',
    category: 'mep_labor',
    categoryLabel: 'MEP Infrastructure (Electrical)',
    unit: 'sq ft',
    formulaDescription: 'Covered Area (sq ft) × 1.0 sq ft',
    civilEngineeringNotes: 'Main Distribution Board (MDB), Schneider/Terasaki circuit breakers, copper grounding bore, AC loops, CAT-6 networking, and energy-saving LED SMD ceiling lights.',
    defaultVarietyId: 'pak_cables_pure_copper',
    calculateQuantity: (area, floors, beds, baths) => Math.round(area),
    varieties: [
      { id: 'pak_cables_pure_copper', name: 'Pakistan Cables 99.9% Pure Copper Wiring + Clipsal / Orange Switches + SMD LEDs', description: 'Highest-safety copper conductors with fire-resistant PVC insulation and branded architectural faceplates.', defaultPricePKR: 260, unit: 'per sq ft covered' },
      { id: 'fast_cables_premium', name: 'Fast Cables Flame Retardant (FR) Copper + OPAL LED Downlights', description: 'Certified flame retardant copper cables with premium LED downlights.', defaultPricePKR: 210, unit: 'per sq ft covered' },
      { id: 'standard_wiring', name: 'Standard Grade Copper Cables + Local Modular Switches', description: 'Commercial grade copper wiring with standard residential switches.', defaultPricePKR: 145, unit: 'per sq ft covered' },
    ],
  },
  {
    id: 'waterproofing',
    name: 'Waterproofing, Termite Proofing & DPC Membrane',
    category: 'mep_labor',
    categoryLabel: 'Structural Protection (Water & Termite)',
    unit: 'sq ft',
    formulaDescription: 'Building Footprint Area (Covered Area ÷ Storeys) + Rooftop Slab',
    civilEngineeringNotes: 'Protects foundation from subterranean termite destruction, provides double DPC barrier against rising dampness, and prevents rooftop rainfall seepage.',
    defaultVarietyId: 'membrane_bitumen_4mm',
    calculateQuantity: (area, floors, beds, baths) => Math.round((area / Math.max(1, floors)) * 1.8),
    varieties: [
      { id: 'membrane_bitumen_4mm', name: '4mm SBS Bitumen Torch-On Membrane + Termite Chemical Injection (Termidor)', description: 'Heavy-duty polyester-reinforced bitumen membrane on rooftop with 10-year anti-termite ground barrier.', defaultPricePKR: 95, unit: 'per sq ft surface' },
      { id: 'chemical_coating_screed', name: 'Elastomeric Cementitious Coating + Mud Phaska Screed + Termite Spray', description: 'Flexible polymer cement waterproofing with traditional mud phaska thermal insulation on roof.', defaultPricePKR: 65, unit: 'per sq ft surface' },
      { id: 'polythene_dpc_basic', name: 'Double Polythene DPC Barrier + Coal Tar Foundation Coating', description: 'Economical damp-proof course layer preventing moisture capillary action in ground walls.', defaultPricePKR: 38, unit: 'per sq ft surface' },
    ],
  },
];

export interface DetailedMaterialItem {
  id: string;
  name: string;
  category: 'grey' | 'finishing' | 'mep_labor';
  categoryLabel: string;
  unit: string;
  quantity: number;
  formulaDescription: string;
  civilEngineeringNotes: string;
  selectedVarietyId: string;
  selectedVarietyName: string;
  selectedVarietyDescription: string;
  unitPricePKR: number;
  lineTotalPKR: number;
  varieties: MaterialVarietyOption[];
}

export interface DetailedBOQResult {
  coveredAreaSqFt: number;
  floors: number;
  bedrooms: number;
  bathrooms: number;
  items: DetailedMaterialItem[];
  greyStructureTotalPKR: number;
  finishingTotalPKR: number;
  mepAndLaborTotalPKR: number;
  subtotalPKR: number;
  contingencyRatePercent: number;
  contingencyPKR: number;
  grandTotalPKR: number;
  ratePerSqFtPKR: number;
  categorySharePercentages: {
    greyPercent: number;
    finishingPercent: number;
    mepLaborPercent: number;
    contingencyPercent: number;
  };
}

export function calculateDetailedBOQ(
  coveredAreaSqFt: number,
  floors: number = 2,
  bedrooms: number = 4,
  bathrooms: number = 4,
  selectedVarieties: Record<string, string> = {},
  customPrices: Record<string, number> = {},
  customQuantities: Record<string, number> = {},
  contingencyRatePercent: number = 7.5
): DetailedBOQResult {
  const safeArea = Math.max(200, coveredAreaSqFt);
  const safeFloors = Math.max(1, floors);
  const safeBeds = Math.max(1, bedrooms);
  const safeBaths = Math.max(1, bathrooms);

  const items: DetailedMaterialItem[] = DETAILED_MATERIALS_CATALOG.map((mat) => {
    const chosenVarietyId = selectedVarieties[mat.id] || mat.defaultVarietyId;
    const varietyOption = mat.varieties.find((v) => v.id === chosenVarietyId) || mat.varieties[0];

    const standardQty = mat.calculateQuantity(safeArea, safeFloors, safeBeds, safeBaths);
    const quantity = customQuantities[mat.id] !== undefined ? customQuantities[mat.id] : standardQty;

    const unitPricePKR = customPrices[mat.id] !== undefined ? customPrices[mat.id] : varietyOption.defaultPricePKR;
    const lineTotalPKR = Math.round(quantity * unitPricePKR);

    return {
      id: mat.id,
      name: mat.name,
      category: mat.category,
      categoryLabel: mat.categoryLabel,
      unit: mat.unit,
      quantity,
      formulaDescription: mat.formulaDescription,
      civilEngineeringNotes: mat.civilEngineeringNotes,
      selectedVarietyId: varietyOption.id,
      selectedVarietyName: varietyOption.name,
      selectedVarietyDescription: varietyOption.description,
      unitPricePKR,
      lineTotalPKR,
      varieties: mat.varieties,
    };
  });

  let greyTotal = 0;
  let finishingTotal = 0;
  let mepLaborTotal = 0;

  items.forEach((item) => {
    if (item.category === 'grey') {
      greyTotal += item.lineTotalPKR;
    } else if (item.category === 'finishing') {
      finishingTotal += item.lineTotalPKR;
    } else {
      mepLaborTotal += item.lineTotalPKR;
    }
  });

  const subtotalPKR = greyTotal + finishingTotal + mepLaborTotal;
  const contingencyPKR = Math.round(subtotalPKR * (contingencyRatePercent / 100));
  const grandTotalPKR = subtotalPKR + contingencyPKR;
  const ratePerSqFtPKR = Math.round(grandTotalPKR / safeArea);

  const greyPercent = parseFloat(((greyTotal / grandTotalPKR) * 100).toFixed(1));
  const finishingPercent = parseFloat(((finishingTotal / grandTotalPKR) * 100).toFixed(1));
  const mepLaborPercent = parseFloat(((mepLaborTotal / grandTotalPKR) * 100).toFixed(1));
  const contingencyPercent = parseFloat(((contingencyPKR / grandTotalPKR) * 100).toFixed(1));

  return {
    coveredAreaSqFt: safeArea,
    floors: safeFloors,
    bedrooms: safeBeds,
    bathrooms: safeBaths,
    items,
    greyStructureTotalPKR: greyTotal,
    finishingTotalPKR: finishingTotal,
    mepAndLaborTotalPKR: mepLaborTotal,
    subtotalPKR,
    contingencyRatePercent,
    contingencyPKR,
    grandTotalPKR,
    ratePerSqFtPKR,
    categorySharePercentages: {
      greyPercent,
      finishingPercent,
      mepLaborPercent,
      contingencyPercent,
    },
  };
}

export interface CostCalculationParams {
  projectId: string;
  projectTitle: string;
  coveredAreaSqFt: number;
  floors: number;
  category: 'economy' | 'standard' | 'premium' | 'luxury';
  city: 'Islamabad/Rawalpindi' | 'Lahore' | 'Karachi' | 'Peshawar' | 'Multan' | 'Faisalabad';
  currency?: 'PKR' | 'USD';
}

export const CITY_FACTORS: Record<string, number> = {
  'Islamabad/Rawalpindi': 1.03,
  'Lahore': 1.00,
  'Karachi': 1.05,
  'Peshawar': 0.96,
  'Multan': 0.95,
  'Faisalabad': 0.94,
};

const BASE_RATE_PER_SQFT: Record<string, { grey: number; finishing: number }> = {
  economy: { grey: 2900, finishing: 2300 }, // Total ~5,200 PKR/sqft
  standard: { grey: 3200, finishing: 3400 }, // Total ~6,600 PKR/sqft
  premium: { grey: 3500, finishing: 4500 }, // Total ~8,000 PKR/sqft
  luxury: { grey: 3900, finishing: 6500 },  // Total ~10,400 PKR/sqft
};

export function calculatePreliminaryCost(params: CostCalculationParams): CostEstimate {
  const {
    projectId,
    projectTitle,
    coveredAreaSqFt,
    floors,
    category,
    city,
    currency = 'PKR',
  } = params;

  const cityFactor = CITY_FACTORS[city] || 1.0;
  const rates = BASE_RATE_PER_SQFT[category] || BASE_RATE_PER_SQFT.standard;

  const adjustedGreyRate = Math.round(rates.grey * cityFactor);
  const adjustedFinishingRate = Math.round(rates.finishing * cityFactor);
  const totalRatePerSqFt = adjustedGreyRate + adjustedFinishingRate;

  const totalCost = Math.round(coveredAreaSqFt * totalRatePerSqFt);
  const greyStructureTotal = Math.round(coveredAreaSqFt * adjustedGreyRate);
  const finishingTotal = totalCost - greyStructureTotal;

  // Breakdown percentages based on standard Pakistan engineering practice (PEC guidelines)
  const breakdown: CostBreakdown = {
    greyStructure: greyStructureTotal,
    foundationAndEarthwork: Math.round(greyStructureTotal * 0.18),
    brickworkMasonry: Math.round(greyStructureTotal * 0.22),
    cementSandCrush: Math.round(greyStructureTotal * 0.26),
    steelRebar: Math.round(greyStructureTotal * 0.34),
    plumbingSanitary: Math.round(finishingTotal * 0.12),
    electricalWiringConduits: Math.round(finishingTotal * 0.14),
    flooringTilesMarbles: Math.round(finishingTotal * 0.24),
    doorsWindowsWoodMetal: Math.round(finishingTotal * 0.22),
    paintFinishingFalseCeiling: Math.round(finishingTotal * 0.14),
    kitchenBathFixtures: Math.round(finishingTotal * 0.14),
    labourCost: Math.round(totalCost * 0.22),
    contingencyAllowance: Math.round(totalCost * 0.05),
  };

  const scenarioMin = Math.round(totalCost * 0.92);
  const scenarioTypical = totalCost;
  const scenarioMax = Math.round(totalCost * 1.14);

  return {
    id: `est_${Date.now()}`,
    projectId,
    projectTitle,
    coveredAreaSqFt,
    floors,
    category,
    regionalCity: city,
    currency,
    ratesDate: 'October 2026',
    breakdown,
    totalEstimatedCostPKR: totalCost,
    costPerSqFtPKR: totalRatePerSqFt,
    scenarioMinPKR: scenarioMin,
    scenarioTypicalPKR: scenarioTypical,
    scenarioMaxPKR: scenarioMax,
    notes: [
      `Cost model configured for ${city} regional market index (Factor ${cityFactor}x).`,
      `Finishing category: ${category.toUpperCase()} specifications with grade-60 steel reinforcement.`,
      `Contingency margin (+5%) incorporated to guard against short-term material inflation.`,
      `Does not include society approval fees, plot acquisition costs, or high-voltage transformer installations.`,
    ],
    createdAt: new Date().toISOString().split('T')[0],
  };
}

export function formatPKR(val: number): string {
  if (val >= 10000000) {
    const crores = (val / 10000000).toFixed(2);
    return `PKR ${crores} Crore`;
  }
  if (val >= 100000) {
    const lakhs = (val / 100000).toFixed(2);
    return `PKR ${lakhs} Lakh`;
  }
  return `PKR ${Math.round(val).toLocaleString('en-PK')}`;
}
