/**
 * ArchiCraft AI - Centralized Backend API Client
 * Connects the React 19 Frontend with Python Architectural Studio (api_server.py)
 */

export interface BackendStatus {
  system: string;
  version: string;
  status: string;
  blender_available: boolean;
  cad_engine_ready: boolean;
  gemini_rag_engine?: boolean;
}

export interface GenerateDesignPayload {
  prompt: string;
  plot_width: number;
  plot_length: number;
  floors?: number;
  bedrooms?: number;
  bathrooms?: number;
  style?: string;
  shape?: string;
  budget_tier?: string;
  currency?: string;
  seed?: number;
  strategy?: string;
  variant_index?: number;
}

class ApiService {
  private baseUrl: string = '';

  /**
   * Ping backend health & readiness
   */
  async getStatus(): Promise<BackendStatus | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/status`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Trigger real procedural AI architectural design synthesis via Python backend
   */
  async generateDesign(payload: GenerateDesignPayload): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let errText = 'Server error';
      try {
        const errJson = await res.json();
        errText = errJson.error || errJson.message || JSON.stringify(errJson);
      } catch {
        errText = await res.text().catch(() => 'Server error');
      }
      throw new Error(`Generation failed (HTTP ${res.status}): ${errText}`);
    }

    const data = await res.json();
    if (data && data.success === false) {
      throw new Error(data.error || 'Architectural generation returned an error');
    }
    return data;
  }

  /**
   * Regenerate variation using diversity engine
   */
  async regenerateDesign(payload: GenerateDesignPayload): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Regeneration failed (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Targeted regeneration on CanonicalFloorPlan (Phase 2)
   */
  async regenerateWithImprovement(params: {
    plan_id: string;
    improvement_text: string;
    base_version?: number;
  }): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Regeneration failed' }));
      throw new Error(err.error || `Regeneration failed (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Fetch version history for a plan (Phase 2)
   */
  async getPlanVersions(planId: string): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/plans/${encodeURIComponent(planId)}/versions`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (!res.ok) return [];
      const data = await res.json();
      return data.versions || [];
    } catch {
      return [];
    }
  }

  /**
   * Restore a historical plan version (Phase 2)
   */
  async restorePlanVersion(planId: string, version: number): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/plans/${encodeURIComponent(planId)}/restore`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ version }),
    });

    if (!res.ok) {
      throw new Error(`Failed to restore version ${version} (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Calculate BOQ cost estimation via backend
   */

  /**
   * Fetch live Pakistan construction material market rates using Gemini AI
   */
  async fetchGeminiMarketRates(apiKey: string, city?: string): Promise<{ success: boolean; source: string; city: string; rates: Record<string, number> }> {
    const res = await fetch(`${this.baseUrl}/api/gemini/market-rates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, city: city || 'Islamabad / Lahore' }),
    });
    if (!res.ok) {
      throw new Error(`Market rates fetch failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  async calculateCost(params: {
    covered_area_sqft: number;
    floors: number;
    bedrooms: number;
    bathrooms: number;
    budget_tier?: string;
    currency?: string;
    custom_unit_prices?: Record<string, number>;
  }): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/cost-estimation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      throw new Error(`Cost calculation failed (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Download real generated export file (AutoCAD DXF, SVG, PDF, Blender .blend)
   */
  async exportFile(format: 'dxf' | 'svg' | 'pdf' | 'blend' | 'obj' | 'png', designData: any): Promise<{ blob: Blob; filename: string }> {
    const endpoint = `/api/export/${format}`;
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(designData),
    });

    if (!res.ok) {
      throw new Error(`Export failed for ${format.toUpperCase()} (HTTP ${res.status})`);
    }

    const disposition = res.headers.get('Content-Disposition') || '';
    let filename = `design_export.${format === 'blend' ? 'blend' : format}`;
    const match = disposition.match(/filename=["']?([^"';]+)["']?/i);
    if (match && match[1]) {
      filename = match[1];
    }

    const blob = await res.blob();
    return { blob, filename };
  }

  /**
   * Fetch templates from backend repository
   */
  /**
   * Save project into the backend database (saved_projects.json)
   */
  async saveProject(projectData: any): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/projects/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(projectData),
    });
    if (!res.ok) throw new Error('Failed to save project to backend database');
    return await res.json();
  }

  /**
   * Fetch saved projects from backend database
   */
  async getProjects(): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/api/projects`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to load projects from backend database');
    return await res.json();
  }

  async getTemplates(): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/api/templates`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to load templates');
    return await res.json();
  }
}

export const apiService = new ApiService();
