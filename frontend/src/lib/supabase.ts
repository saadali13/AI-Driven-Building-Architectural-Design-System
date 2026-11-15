import { createClient, SupabaseClient } from '@supabase/supabase-js';
import type { Project } from '../types';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const supabase: SupabaseClient | null =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null;

/**
 * Synchronizes a project record to Supabase if credentials are configured.
 * Gracefully no-ops in local/offline mode.
 */
export async function syncProjectToSupabase(project: Project): Promise<void> {
  if (!supabase) {
    return;
  }

  try {
    const { error } = await supabase.from('projects').upsert(
      {
        id: project.id,
        title: project.title,
        type: project.type,
        owner_id: project.ownerId,
        owner_name: project.ownerName,
        plot_preset: project.plotPreset,
        plot_width_ft: project.plotWidthFt,
        plot_length_ft: project.plotLengthFt,
        plot_area_sqft: project.plotAreaSqFt,
        floors: project.floors,
        bedrooms: project.bedrooms,
        bathrooms: project.bathrooms,
        style: project.style,
        status: project.status,
        created_at: project.createdAt,
        updated_at: project.updatedAt,
      },
      { onConflict: 'id' }
    );

    if (error) {
      console.warn('[Supabase] Project sync warning:', error.message);
    }
  } catch (err) {
    console.warn('[Supabase] Failed to sync project:', err);
  }
}

