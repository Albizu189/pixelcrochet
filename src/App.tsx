import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft, ArrowRight, BookOpen, Camera, Check, ChevronLeft, CircleHelp,
  ExternalLink, FilePenLine, FolderKanban, Github, Home, Image as ImageIcon,
  Info, Languages, ListChecks, Menu, Moon, MoreHorizontal, Palette, Pencil,
  Plus, Ruler, Save, Sun, Trash2, WifiOff, X,
} from 'lucide-react';
import './App.css';
import { copy, techniqueName, type Copy } from './i18n';
import { db, newDraft } from './db';
import type { Draft, Language, Project, RouteName, Technique, Theme } from './types';
import { CameraDialog } from './components/CameraDialog';
import { RoiEditor } from './components/RoiEditor';
import { PatternGrid } from './components/PatternGrid';
import { LoadingOverlay } from './components/LoadingOverlay';
import { imageFileToDataUrl, stepsFromInstructions } from './lib/image';
import { runEngine, type EngineStage } from './lib/engine';

const REPO_URL = 'https://github.com/Albizu189/pixelcrochet';
const HOOKS = ['1 mm', '1,75 mm', '2 mm', '2,5 mm', '3 mm', '3,5 mm', '4 mm'];

type Route = { name: RouteName; id?: string };
type EngineHandle = ReturnType<typeof runEngine>;

function routeFromHash(): Route {
  const raw = window.location.hash.replace(/^#\/?/, '');
  const [name, query] = raw.split('?');
  const id = new URLSearchParams(query || '').get('id') || undefined;
  const allowed: RouteName[] = ['home', 'new', 'projects', 'drafts', 'project', 'more', 'help', 'about'];
  return { name: allowed.includes(name as RouteName) ? name as RouteName : 'home', id };
}

function formatDate(value: string, language: Language) {
  return new Intl.DateTimeFormat(language === 'es' ? 'es' : 'en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

function PhotoField({ kind, image, t, onImage, onCamera }: { kind: 'pattern' | 'yarn'; image: string | null; t: Copy; onImage: (value: string | null) => void; onCamera: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  async function selected(file?: File) {
    if (!file) return;
    setBusy(true);
    try { onImage(await imageFileToDataUrl(file)); } finally { setBusy(false); }
  }
  return <div className={`photo-field ${image ? 'has-image' : ''}`}>
    <div className="photo-preview">
      {image ? <img src={image} alt={kind === 'pattern' ? t.patternPhoto : t.yarnPhoto} /> : <div className="photo-placeholder">{kind === 'pattern' ? <ImageIcon /> : <Palette />}<span>{kind === 'pattern' ? t.patternPhoto : t.yarnPhoto}</span></div>}
    </div>
    <div className="photo-field-copy"><h3>{kind === 'pattern' ? t.patternPhoto : t.yarnPhoto}</h3>{image && <button className="text-button danger" onClick={() => onImage(null)}><Trash2 size={17} />{t.remove}</button>}</div>
    <div className="photo-actions">
      <button className="secondary-button" onClick={onCamera} disabled={busy}><Camera size={19} />{t.camera}</button>
      <button className="secondary-button" onClick={() => input.current?.click()} disabled={busy}><ImageIcon size={19} />{image ? t.change : t.gallery}</button>
    </div>
    <input ref={input} className="visually-hidden" type="file" accept="image/*" onChange={(event) => selected(event.target.files?.[0])} />
  </div>;
}

function EmptyState({ icon, text, action, onAction }: { icon: React.ReactNode; text: string; action?: string; onAction?: () => void }) {
  return <div className="empty-state"><div className="empty-icon">{icon}</div><p>{text}</p>{action && <button className="primary-button" onClick={onAction}><Plus size={19} />{action}</button>}</div>;
}

function App() {
  const [language, setLanguage] = useState<Language>(() => localStorage.getItem('pc-language') === 'en' ? 'en' : 'es');
  const [theme, setTheme] = useState<Theme>(() => localStorage.getItem('pc-theme') === 'dark' ? 'dark' : 'light');
  const t = copy(language);
  const [route, setRoute] = useState<Route>(routeFromHash);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loadingStage, setLoadingStage] = useState<EngineStage | null>(null);
  const [cameraTarget, setCameraTarget] = useState<'pattern' | 'yarn' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ text: string; action: () => void } | null>(null);
  const [editProject, setEditProject] = useState(false);
  const [editName, setEditName] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [projectTab, setProjectTab] = useState<'instructions' | 'pattern' | 'materials'>('instructions');
  const [viewStep, setViewStep] = useState(0);
  const engine = useRef<EngineHandle | null>(null);

  const refresh = useCallback(async () => {
    const [draftValues, projectValues] = await Promise.all([db.drafts(), db.projects()]);
    setDrafts(draftValues.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)));
    setProjects(projectValues.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)));
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    localStorage.setItem('pc-language', language);
    document.documentElement.lang = language;
  }, [language]);
  useEffect(() => {
    localStorage.setItem('pc-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#102E2D' : '#1A4A48');
  }, [theme]);
  useEffect(() => {
    const change = () => { setRoute(routeFromHash()); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', change);
    if (!window.location.hash) window.history.replaceState(null, '', '#home');
    return () => window.removeEventListener('hashchange', change);
  }, []);

  useEffect(() => {
    if (route.name === 'new') {
      if (route.id) db.draft(route.id).then((value) => { if (value) setDraft(value); else navigate('drafts'); });
      else {
        const value = newDraft();
        setDraft(value);
        db.saveDraft(value).then(refresh);
        window.history.replaceState(null, '', `#new?id=${value.id}`);
        setRoute({ name: 'new', id: value.id });
      }
    } else setDraft(null);
    if (route.name === 'project' && route.id) {
      db.project(route.id).then((value) => {
        if (!value) { navigate('projects'); return; }
        setProject(value);
        setViewStep(value.completedStep);
        setProjectTab('instructions');
      });
    } else setProject(null);
  }, [route.name, route.id]);

  useEffect(() => {
    if (!draft) return;
    const timer = window.setTimeout(() => {
      db.saveDraft({ ...draft, updatedAt: new Date().toISOString() }).then(refresh);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [draft, refresh]);
  useEffect(() => {
    if (!draft) return;
    const persist = () => db.saveDraft({ ...draft, updatedAt: new Date().toISOString() });
    window.addEventListener('pagehide', persist);
    return () => window.removeEventListener('pagehide', persist);
  }, [draft]);

  function navigate(name: RouteName, id?: string, preserveDraft = true) {
    if (draft && preserveDraft) void db.saveDraft({ ...draft, updatedAt: new Date().toISOString() });
    const hash = `#${name}${id ? `?id=${id}` : ''}`;
    if (window.location.hash === hash) setRoute({ name, id });
    else window.location.hash = hash;
  }
  function startNew() { navigate('new'); }
  function goBack() {
    if (['projects', 'drafts', 'more', 'help', 'about'].includes(route.name)) navigate('home');
    else if (window.history.length > 1) window.history.back();
    else navigate('home');
  }
  function updateDraft(patch: Partial<Draft>) { setDraft((value) => value ? { ...value, ...patch } : value); }
  function updateProject(patch: Partial<Project>) {
    if (!project) return;
    const updated = { ...project, ...patch, updatedAt: new Date().toISOString() };
    setProject(updated);
    void db.saveProject(updated).then(refresh);
  }
  function notifyError(message: string) {
    setError(message);
    window.setTimeout(() => setError(null), 6500);
  }

  async function extractPalette() {
    if (!draft?.yarnImage) return;
    setLoadingStage('runtime');
    engine.current = runEngine('palette', { ...draft }, setLoadingStage);
    try {
      const result = await engine.current.promise;
      updateDraft({ palette: result.palette || [], capacities: Array(result.palette?.length || 0).fill(null) });
    } catch (reason) { notifyError(reason instanceof Error ? reason.message : t.tryAgain); }
    finally { setLoadingStage(null); engine.current = null; }
  }

  async function generateProject() {
    if (!draft?.patternImage || !draft.yarnImage || !draft.palette.length) { notifyError(t.requiredImages); return; }
    if (!draft.name.trim()) { notifyError(t.requiredName); return; }
    const total = draft.width * draft.height;
    const available = draft.capacities.reduce<number>((sum, value) => sum + (value === null ? total : value), 0);
    if (available < total) { notifyError(t.capacityError); return; }
    setLoadingStage('runtime');
    engine.current = runEngine('generate', { ...draft }, setLoadingStage);
    try {
      const result = await engine.current.promise;
      const now = new Date().toISOString();
      const generated: Project = {
        ...draft, name: draft.name.trim(), palette: result.palette, result,
        updatedAt: now, completedStep: 0, lastCompletedAt: null, notes: '',
      };
      await db.saveProject(generated);
      await db.deleteDraft(draft.id);
      await refresh();
      setLoadingStage(null);
      engine.current = null;
      navigate('project', generated.id, false);
    } catch (reason) {
      notifyError(reason instanceof Error ? reason.message : t.tryAgain);
      setLoadingStage(null);
      engine.current = null;
    }
  }

  async function captured(blob: Blob) {
    if (!cameraTarget || !draft) return;
    try {
      const data = await imageFileToDataUrl(blob);
      updateDraft(cameraTarget === 'pattern' ? { patternImage: data } : { yarnImage: data, palette: [] });
      setCameraTarget(null);
    } catch { notifyError(t.cameraError); }
  }

  function deleteDraft(id: string) {
    setConfirmAction({ text: t.deleteDraftQuestion, action: async () => {
      await db.deleteDraft(id); await refresh(); setConfirmAction(null);
      if (route.name === 'new') navigate('drafts');
    } });
  }
  function deleteProject(id: string) {
    setConfirmAction({ text: t.deleteProjectQuestion, action: async () => {
      await db.deleteProject(id); await refresh(); setConfirmAction(null);
      if (route.name === 'project') navigate('projects');
    } });
  }

  const instructionSteps = useMemo(() => {
    if (!project) return [];
    const key = project.technique === 'c2c' ? 'c2c' : 'rows';
    return stepsFromInstructions(project.result.instructions[language][key], key);
  }, [project, language]);
  useEffect(() => { setViewStep((value) => Math.min(value, Math.max(0, instructionSteps.length - 1))); }, [instructionSteps.length]);

  function completeStep() {
    if (!project || !instructionSteps.length) return;
    const completed = Math.max(project.completedStep, viewStep + 1);
    const now = new Date().toISOString();
    updateProject({ completedStep: completed, lastCompletedAt: now });
    setViewStep(Math.min(viewStep + 1, instructionSteps.length - 1));
  }

  function ThemeLanguageControls() {
    return <div className="preference-controls">
      <button className="preference-button" onClick={() => setLanguage(language === 'es' ? 'en' : 'es')} aria-label={t.language}><Languages size={18} /><span>{language === 'es' ? 'ES' : 'EN'}</span></button>
      <button className="preference-button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={theme === 'light' ? t.dark : t.light}>{theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}<span>{theme === 'light' ? t.dark : t.light}</span></button>
    </div>;
  }

  function Navigation() {
    return <>
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate('home')}><img src="/icons/icon.svg" alt="" /><span>PixelCrochet<small>{t.tagline}</small></span></button>
        <button className="primary-button new-pattern-button" onClick={startNew}><Plus size={20} />{t.newProject}</button>
        <nav className="side-nav" aria-label={t.home}>
          <NavButton name="home" icon={<Home />} label={t.home} />
          <NavButton name="projects" icon={<FolderKanban />} label={t.projects} count={projects.length} />
          <NavButton name="drafts" icon={<FilePenLine />} label={t.drafts} count={drafts.length} />
          <NavButton name="help" icon={<CircleHelp />} label={t.help} />
          <NavButton name="about" icon={<Info />} label={t.about} />
        </nav>
        <div className="sidebar-bottom"><ThemeLanguageControls /><p><WifiOff size={15} />{t.saving}</p></div>
      </aside>
      <header className="mobile-header">
        <button className="mobile-brand" onClick={() => navigate('home')}><img src="/icons/icon.svg" alt="" /><span>PixelCrochet</span></button>
        <div><button className="icon-button" onClick={() => setLanguage(language === 'es' ? 'en' : 'es')} aria-label={t.language}><Languages /></button><button className="icon-button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={t.theme}>{theme === 'light' ? <Moon /> : <Sun />}</button></div>
      </header>
      <nav className="bottom-nav" aria-label={t.home}>
        <NavButton name="home" icon={<Home />} label={t.home} />
        <NavButton name="projects" icon={<FolderKanban />} label={t.projects} />
        <button className="bottom-create" onClick={startNew}><Plus /><span>{t.newProject}</span></button>
        <NavButton name="drafts" icon={<FilePenLine />} label={t.drafts} />
        <NavButton name="more" icon={<MoreHorizontal />} label={t.more} />
      </nav>
    </>;
  }

  function NavButton({ name, icon, label, count }: { name: RouteName; icon: React.ReactNode; label: string; count?: number }) {
    const active = route.name === name || (name === 'projects' && route.name === 'project') || (name === 'drafts' && route.name === 'new');
    return <button className={`nav-button ${active ? 'active' : ''}`} onClick={() => navigate(name)}>{icon}<span>{label}</span>{count !== undefined && <b>{count}</b>}</button>;
  }

  function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
    return <div className="page-header"><button className="back-button" onClick={goBack}><ArrowLeft size={20} />{t.back}</button><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>;
  }

  function HomePage() {
    const recentProjects = projects.slice(0, 3);
    const recentDrafts = drafts.slice(0, 2);
    return <div className="home-page">
      <section className="hero">
        <div className="hero-copy"><span className="hand-label">{t.tagline}</span><h1>{t.heroTitle}</h1><p>{t.heroText}</p><button className="primary-button hero-button" onClick={startNew}>{t.start}<ArrowRight size={20} /></button></div>
        <div className="hero-art" aria-hidden="true"><div className="pixel-swatch one" /><div className="pixel-swatch two" /><img src="/icons/icon.svg" alt="" /><svg viewBox="0 0 260 80"><path d="M4 56c47-51 80 35 126-8s77 22 125-18" /></svg></div>
      </section>
      <section className="offline-note"><WifiOff /><div><h2>{t.offline}</h2><p>{t.offlineText}</p></div></section>
      <section className="home-section"><div className="section-heading"><h2>{t.recentDrafts}</h2>{drafts.length > 2 && <button className="text-button" onClick={() => navigate('drafts')}>{t.drafts}<ArrowRight size={17} /></button>}</div>
        {recentDrafts.length ? <div className="project-list">{recentDrafts.map((item) => <DraftRow key={item.id} item={item} />)}</div> : <p className="muted-copy">{t.emptyDrafts}</p>}
      </section>
      <section className="home-section"><div className="section-heading"><h2>{t.recentProjects}</h2>{projects.length > 3 && <button className="text-button" onClick={() => navigate('projects')}>{t.projects}<ArrowRight size={17} /></button>}</div>
        {recentProjects.length ? <div className="project-grid">{recentProjects.map((item) => <ProjectCard key={item.id} item={item} />)}</div> : <p className="muted-copy">{t.emptyProjects}</p>}
      </section>
    </div>;
  }

  function DraftRow({ item }: { item: Draft }) {
    return <article className="draft-row">
      <button className="draft-main" onClick={() => navigate('new', item.id)}><div className="draft-thumb">{item.patternImage ? <img src={item.patternImage} alt="" /> : <FilePenLine />}</div><div><h3>{item.name || `${t.drafts} · ${formatDate(item.createdAt, language)}`}</h3><p>{t.updated}: {formatDate(item.updatedAt, language)}</p><span className="step-chip">{item.step}/3 · {techniqueName(t, item.technique)}</span></div><ArrowRight /></button>
      <button className="icon-button danger" onClick={() => deleteDraft(item.id)} aria-label={t.delete}><Trash2 /></button>
    </article>;
  }

  function ProjectCard({ item }: { item: Project }) {
    const steps = stepsFromInstructions(item.result.instructions[language][item.technique === 'c2c' ? 'c2c' : 'rows'], item.technique === 'c2c' ? 'c2c' : 'rows');
    const percent = steps.length ? Math.round(item.completedStep / steps.length * 100) : 0;
    return <article className="project-card">
      <button className="project-card-main" onClick={() => navigate('project', item.id)}><img src={item.result.patternImage} alt={item.name} /><div className="project-card-copy"><span className="technique-label">{techniqueName(t, item.technique)}</span><h3>{item.name}</h3><div className="mini-progress"><span style={{ width: `${percent}%` }} /></div><p>{percent}% · {item.completedStep}/{steps.length} {t.instructions.toLowerCase()}</p></div></button>
      <div className="card-actions"><button className="icon-button" onClick={() => { setProject(item); setEditName(item.name); setEditNotes(item.notes); setEditProject(true); }} aria-label={t.rename}><Pencil /></button><button className="icon-button danger" onClick={() => deleteProject(item.id)} aria-label={t.delete}><Trash2 /></button></div>
    </article>;
  }

  function NewProjectPage() {
    if (!draft) return <div className="page-loading"><span className="status-dot" /></div>;
    return <div className="editor-page">
      <PageHeader title={draft.name || t.newProject} subtitle={`${t.step} ${draft.step} ${t.of} 3`} />
      <div className="stepper" aria-label={`${t.step} ${draft.step}`}>{[1, 2, 3].map((step) => <button key={step} className={draft!.step >= step ? 'reached' : ''} onClick={() => { if (step < draft!.step) updateDraft({ step: step as 1 | 2 | 3 }); }} disabled={step > draft!.step} aria-label={`${t.step} ${step}`}><span>{draft!.step > step ? <Check size={16} /> : step}</span></button>)}</div>
      {draft.step === 1 && <section className="editor-section"><div className="section-intro"><span className="section-number">01</span><div><h2>{t.photosTitle}</h2><p>{t.photosText}</p></div></div><div className="photo-grid"><PhotoField kind="pattern" image={draft.patternImage} t={t} onImage={(patternImage) => updateDraft({ patternImage })} onCamera={() => setCameraTarget('pattern')} /><PhotoField kind="yarn" image={draft.yarnImage} t={t} onImage={(yarnImage) => updateDraft({ yarnImage, palette: [] })} onCamera={() => setCameraTarget('yarn')} /></div><div className="editor-actions"><button className="secondary-button" onClick={() => navigate('home')}><Save size={19} />{t.saveExit}</button><button className="primary-button" onClick={() => { if (!draft.patternImage || !draft.yarnImage) notifyError(t.requiredImages); else updateDraft({ step: 2 }); }}>{t.next}<ArrowRight size={19} /></button></div></section>}
      {draft.step === 2 && <section className="editor-section"><div className="section-intro"><span className="section-number">02</span><div><h2>{t.paletteTitle}</h2><p>{t.paletteText}</p></div></div><div className="palette-workspace"><div><RoiEditor image={draft.yarnImage!} roi={draft.roi} onChange={(roi) => updateDraft({ roi, palette: [] })} /><div className="field compact-field"><label htmlFor="color-count">{t.colors}</label><div className="number-stepper"><button onClick={() => updateDraft({ colorCount: Math.max(2, draft.colorCount - 1), palette: [] })} disabled={draft.colorCount <= 2}>−</button><input id="color-count" type="number" min="2" max="8" value={draft.colorCount} onChange={(event) => updateDraft({ colorCount: Math.max(2, Math.min(8, Number(event.target.value))), palette: [] })} /><button onClick={() => updateDraft({ colorCount: Math.min(8, draft.colorCount + 1), palette: [] })} disabled={draft.colorCount >= 8}>+</button></div></div><button className="primary-button extract-button" onClick={extractPalette}><Palette size={19} />{draft.palette.length ? t.extract : t.extract}</button></div>
        <div className="palette-results">{draft.palette.length ? <><h3>{t.paletteReady}</h3><div className="capacity-list">{draft.palette.map((color, index) => <div className="capacity-row" key={`${color.hex}-${index}`}><span className="large-swatch" style={{ backgroundColor: color.hex }} /><div><strong>{t.step === 'Paso' ? 'Color' : 'Color'} {index + 1}</strong><small>{color.hex}</small></div><label><span>{t.pixels}</span><input type="number" min="0" placeholder={t.unlimited} value={draft.capacities[index] ?? ''} onChange={(event) => { const capacities = [...draft.capacities]; capacities[index] = event.target.value === '' ? null : Math.max(0, Number(event.target.value)); updateDraft({ capacities }); }} /></label></div>)}</div></> : <div className="palette-empty"><Palette /><p>{t.paletteText}</p></div>}</div></div>
        <div className="editor-actions"><button className="secondary-button" onClick={() => updateDraft({ step: 1 })}><ChevronLeft size={19} />{t.back}</button><button className="primary-button" onClick={() => draft.palette.length ? updateDraft({ step: 3 }) : notifyError(t.requiredPalette)}>{t.next}<ArrowRight size={19} /></button></div></section>}
      {draft.step === 3 && <section className="editor-section"><div className="section-intro"><span className="section-number">03</span><div><h2>{t.settingsTitle}</h2><p>{t.originalCode}</p></div></div><div className="settings-form"><div className="field full-field"><label htmlFor="project-name">{t.projectName}</label><input id="project-name" value={draft.name} placeholder={t.namePlaceholder} onChange={(event) => updateDraft({ name: event.target.value })} maxLength={70} /></div><fieldset className="technique-field"><legend>{t.technique}</legend><div className="technique-options">{(['tapestry', 'intarsia', 'c2c'] as Technique[]).map((technique) => <button key={technique} className={draft.technique === technique ? 'selected' : ''} onClick={() => updateDraft({ technique })}><span className={`technique-icon ${technique}`} aria-hidden="true" />{techniqueName(t, technique)}<Check size={18} /></button>)}</div></fieldset><div className="form-row"><div className="field"><label htmlFor="width">{t.width}</label><input id="width" type="number" min="4" max="80" value={draft.width} onChange={(event) => updateDraft({ width: Math.max(4, Math.min(80, Number(event.target.value))) })} /></div><div className="field"><label htmlFor="height">{t.height}</label><input id="height" type="number" min="4" max="80" value={draft.height} onChange={(event) => updateDraft({ height: Math.max(4, Math.min(80, Number(event.target.value))) })} /></div></div><div className="field"><label htmlFor="hook">{t.hook}</label><select id="hook" value={draft.hookIndex} onChange={(event) => updateDraft({ hookIndex: Number(event.target.value) })}>{HOOKS.map((hook, index) => <option key={hook} value={index}>{hook}</option>)}</select></div><div className="selected-palette">{draft.palette.map((color, index) => <span key={index} style={{ backgroundColor: color.hex }} title={`${index + 1}: ${color.hex}`} />)}</div></div><div className="editor-actions"><button className="secondary-button" onClick={() => updateDraft({ step: 2 })}><ChevronLeft size={19} />{t.back}</button><button className="primary-button generate-button" onClick={generateProject}><ListChecks size={20} />{t.generate}</button></div></section>}
    </div>;
  }

  function ProjectsPage() {
    return <div className="list-page"><PageHeader title={t.projectsTitle} subtitle={`${projects.length} · ${t.saving}`} />{projects.length ? <div className="project-grid large-grid">{projects.map((item) => <ProjectCard key={item.id} item={item} />)}</div> : <EmptyState icon={<FolderKanban />} text={t.emptyProjects} action={t.start} onAction={startNew} />}</div>;
  }
  function DraftsPage() {
    return <div className="list-page"><PageHeader title={t.draftsTitle} subtitle={`${drafts.length} · ${t.saving}`} />{drafts.length ? <div className="project-list">{drafts.map((item) => <DraftRow key={item.id} item={item} />)}</div> : <EmptyState icon={<FilePenLine />} text={t.emptyDrafts} action={t.newProject} onAction={startNew} />}</div>;
  }

  function ProjectPage() {
    if (!project) return <div className="page-loading"><span className="status-dot" /></div>;
    const percent = instructionSteps.length ? Math.round(project.completedStep / instructionSteps.length * 100) : 0;
    const current = instructionSteps[viewStep];
    const activeRow = project.technique !== 'c2c' && viewStep > 0 && viewStep <= project.result.labels.length ? project.result.labels.length - viewStep : undefined;
    return <div className="project-page"><PageHeader title={project.name} subtitle={`${techniqueName(t, project.technique)} · ${project.width} × ${project.height}`} />
      <div className="project-toolbar"><div className="progress-summary"><div><strong>{percent}%</strong><span>{t.progress}</span></div><div className="progress-track"><span style={{ width: `${percent}%` }} /></div><small>{project.completedStep}/{instructionSteps.length}</small></div><div className="toolbar-actions"><button className="secondary-button" onClick={() => { setEditName(project.name); setEditNotes(project.notes); setEditProject(true); }}><Pencil size={18} />{t.edit}</button><button className="icon-button danger" onClick={() => deleteProject(project.id)} aria-label={t.delete}><Trash2 /></button></div></div>
      <div className="project-tabs" role="tablist"><button role="tab" aria-selected={projectTab === 'instructions'} className={projectTab === 'instructions' ? 'active' : ''} onClick={() => setProjectTab('instructions')}><ListChecks />{t.instructions}</button><button role="tab" aria-selected={projectTab === 'pattern'} className={projectTab === 'pattern' ? 'active' : ''} onClick={() => setProjectTab('pattern')}><Menu />{t.pattern}</button><button role="tab" aria-selected={projectTab === 'materials'} className={projectTab === 'materials' ? 'active' : ''} onClick={() => setProjectTab('materials')}><Ruler />{t.materials}</button></div>
      {projectTab === 'instructions' && <section className="instruction-workspace"><div className="instruction-pattern"><PatternGrid labels={project.result.labels} palette={project.result.palette} activeRow={activeRow} label={t.pattern} /><div className="pattern-legend">{project.result.palette.map((color, index) => <span key={index}><i style={{ background: color.hex }} />{index + 1}</span>)}</div></div><div className="step-panel"><div className="step-counter"><span>{current?.label || `${t.step} ${viewStep + 1}`}</span><small>{t.step} {viewStep + 1} {t.of} {instructionSteps.length}</small></div><div className="current-instruction">{current?.colorIndexes.length ? <div className="instruction-colors">{[...new Set(current.colorIndexes)].map((index) => <span key={index} style={{ background: project.result.palette[index - 1]?.hex }} title={`${index}`} />)}</div> : null}<p>{current?.text}</p></div><div className="step-actions"><button className="secondary-button" onClick={() => setViewStep(Math.max(0, viewStep - 1))} disabled={viewStep === 0}><ChevronLeft />{t.previous}</button><button className="primary-button" onClick={completeStep} disabled={project.completedStep >= instructionSteps.length && viewStep >= instructionSteps.length - 1}><Check />{project.completedStep >= instructionSteps.length ? t.completed : t.completeNext}</button></div><div className="last-completed"><Save size={17} /><div><strong>{t.lastSaved}</strong><p>{project.lastCompletedAt ? formatDate(project.lastCompletedAt, language) : t.noProgress}</p></div></div></div></section>}
      {projectTab === 'pattern' && <section className="full-pattern"><div><PatternGrid labels={project.result.labels} palette={project.result.palette} label={t.pattern} /></div><div className="pattern-details"><h2>{t.paletteTitle}</h2>{project.result.palette.map((color, index) => <div className="material-row" key={index}><span className="large-swatch" style={{ background: color.hex }} /><strong>{index + 1} · {color.hex}</strong><span>{project.result.pixelCounts[index]} px</span></div>)}</div></section>}
      {projectTab === 'materials' && <section className="materials-page"><div className="materials-head"><Ruler /><div><h2>{t.meters}</h2><p>{t.estimatedSize}: <strong>{project.result.dimensions[project.technique === 'c2c' ? 'c2c' : 'rows'].join(' × ')} cm</strong></p></div></div><div className="material-list">{project.result.palette.map((color, index) => <div className="material-row" key={index}><span className="large-swatch" style={{ background: color.hex }} /><div><strong>Color {index + 1}</strong><small>{color.hex} · {project.result.pixelCounts[index]} px</small></div><b>{project.result.meters[project.technique][index].toFixed(2)} m</b></div>)}</div><div className="notes-block"><label htmlFor="project-notes">{t.notes}</label><textarea id="project-notes" value={project.notes} placeholder={t.notesPlaceholder} onChange={(event) => updateProject({ notes: event.target.value })} rows={5} /></div></section>}
    </div>;
  }

  function MorePage() {
    return <div className="more-page"><PageHeader title={t.more} /><div className="more-links"><button onClick={() => navigate('help')}><CircleHelp /><span>{t.help}<ArrowRight /></span></button><button onClick={() => navigate('about')}><Info /><span>{t.about}<ArrowRight /></span></button><a href={REPO_URL} target="_blank" rel="noreferrer"><Github /><span>{t.repo}<ExternalLink /></span></a></div><SettingsPanel /></div>;
  }
  function SettingsPanel() {
    return <section className="settings-panel"><h2>{t.settings}</h2><div className="setting-row"><div><strong>{t.language}</strong><p>{t.language === 'Language' ? 'App and generated instructions' : 'App e instrucciones generadas'}</p></div><div className="segmented"><button className={language === 'es' ? 'active' : ''} onClick={() => setLanguage('es')}>{t.spanish}</button><button className={language === 'en' ? 'active' : ''} onClick={() => setLanguage('en')}>{t.english}</button></div></div><div className="setting-row"><div><strong>{t.theme}</strong></div><div className="segmented"><button className={theme === 'light' ? 'active' : ''} onClick={() => setTheme('light')}><Sun size={17} />{t.light}</button><button className={theme === 'dark' ? 'active' : ''} onClick={() => setTheme('dark')}><Moon size={17} />{t.dark}</button></div></div><div className="local-data-note"><WifiOff /><div><strong>{t.localData}</strong><p>{t.localDataText}</p></div></div><div className="local-data-note"><BookOpen /><div><strong>{t.install}</strong><p>{t.installText}</p></div></div></section>;
  }
  function HelpPage() {
    return <div className="article-page"><PageHeader title={t.helpTitle} subtitle={t.helpIntro} /><div className="help-list">{t.helpSteps.map((step, index) => <section key={index}><span>{String(index + 1).padStart(2, '0')}</span><p>{step}</p></section>)}</div><aside className="tip-box"><Camera /><div><h2>{t.helpTips}</h2><p>{t.helpTipText}</p></div></aside><button className="primary-button" onClick={startNew}><Plus />{t.start}</button></div>;
  }
  function AboutPage() {
    return <div className="article-page about-page"><PageHeader title={t.aboutTitle} /><div className="thesis-card"><img src="/icons/icon.svg" alt="" /><div><span>{t.about}</span><h2>{t.aboutAuthor}</h2><p>Universidad de La Habana · 2026</p></div></div><p className="article-body">{t.aboutBody}</p><div className="technique-mini"><span>Tapestry</span><span>Intarsia</span><span>C2C</span></div><p className="article-body">{t.collaboration}</p><a className="primary-button repo-button" href={REPO_URL} target="_blank" rel="noreferrer"><Github />{t.repo}<ExternalLink size={18} /></a><div className="settings-inline"><SettingsPanel /></div></div>;
  }

  return <div className="app-shell">
    <Navigation />
    <main className="app-main">
      {route.name === 'home' && <HomePage />}
      {route.name === 'new' && <NewProjectPage />}
      {route.name === 'projects' && <ProjectsPage />}
      {route.name === 'drafts' && <DraftsPage />}
      {route.name === 'project' && <ProjectPage />}
      {route.name === 'more' && <MorePage />}
      {route.name === 'help' && <HelpPage />}
      {route.name === 'about' && <AboutPage />}
      <footer className="app-footer"><span>PixelCrochet</span><span>·</span><button onClick={() => navigate('about')}>Erika Torres Figueiras · 2026</button></footer>
    </main>
    {cameraTarget && <CameraDialog t={t} onCapture={captured} onClose={() => setCameraTarget(null)} />}
    {loadingStage && <LoadingOverlay t={t} stage={loadingStage} onCancel={() => { engine.current?.cancel(); engine.current = null; setLoadingStage(null); }} />}
    {confirmAction && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setConfirmAction(null); }}><section className="confirm-dialog" role="alertdialog" aria-modal="true" aria-label={t.confirm}><div className="warning-icon"><Trash2 /></div><h2>{t.confirm}</h2><p>{confirmAction.text}</p><div><button className="secondary-button" onClick={() => setConfirmAction(null)}>{t.cancel}</button><button className="danger-button" onClick={confirmAction.action}>{t.delete}</button></div></section></div>}
    {editProject && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setEditProject(false); }}><section className="edit-dialog" role="dialog" aria-modal="true" aria-label={t.editName}><div className="dialog-head"><h2>{t.editName}</h2><button className="icon-button" onClick={() => setEditProject(false)} aria-label={t.close}><X /></button></div><div className="field"><label htmlFor="edit-name">{t.projectName}</label><input id="edit-name" value={editName} onChange={(event) => setEditName(event.target.value)} /></div><div className="field"><label htmlFor="edit-notes">{t.notes}</label><textarea id="edit-notes" value={editNotes} onChange={(event) => setEditNotes(event.target.value)} rows={4} /></div><button className="primary-button" onClick={() => { if (!editName.trim()) { notifyError(t.requiredName); return; } if (project && projects.some((item) => item.id === project.id)) updateProject({ name: editName.trim(), notes: editNotes }); else { const target = projects.find((item) => item.name === project?.name); if (target) void db.saveProject({ ...target, name: editName.trim(), notes: editNotes, updatedAt: new Date().toISOString() }).then(refresh); } setEditProject(false); }}>{t.save}</button></section></div>}
    {error && <div className="error-toast" role="alert"><Info /><div><strong>{t.error}</strong><p>{error}</p></div><button className="icon-button" onClick={() => setError(null)} aria-label={t.close}><X /></button></div>}
  </div>;
}

export default App;
