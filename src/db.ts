import { openDB, type DBSchema } from 'idb';
import type { Draft, Project } from './types';

interface PixelDB extends DBSchema {
  drafts: { key: string; value: Draft; indexes: { updatedAt: string } };
  projects: { key: string; value: Project; indexes: { updatedAt: string } };
}

const dbPromise = openDB<PixelDB>('pixelcrochet', 1, {
  upgrade(db) {
    const drafts = db.createObjectStore('drafts', { keyPath: 'id' });
    drafts.createIndex('updatedAt', 'updatedAt');
    const projects = db.createObjectStore('projects', { keyPath: 'id' });
    projects.createIndex('updatedAt', 'updatedAt');
  },
});

export const db = {
  async drafts() { return (await dbPromise).getAllFromIndex('drafts', 'updatedAt'); },
  async projects() { return (await dbPromise).getAllFromIndex('projects', 'updatedAt'); },
  async draft(id: string) { return (await dbPromise).get('drafts', id); },
  async project(id: string) { return (await dbPromise).get('projects', id); },
  async saveDraft(value: Draft) { return (await dbPromise).put('drafts', value); },
  async saveProject(value: Project) { return (await dbPromise).put('projects', value); },
  async deleteDraft(id: string) { return (await dbPromise).delete('drafts', id); },
  async deleteProject(id: string) { return (await dbPromise).delete('projects', id); },
};

export function newDraft(): Draft {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(), name: '', createdAt: now, updatedAt: now, step: 1,
    patternImage: null, yarnImage: null,
    roi: { x: 20, y: 15, w: 360, h: 270 }, colorCount: 3, palette: [],
    capacities: [], width: 32, height: 32, technique: 'tapestry', hookIndex: 3,
  };
}
