import sys

top_half = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AEGIS Defense System</title>
    <!-- Beautiful, human-centric Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            color: #334155; 
            font-family: 'Outfit', sans-serif; 
            margin: 0; 
            -webkit-font-smoothing: antialiased;
        }
        
        .font-mono { font-family: 'JetBrains Mono', monospace; }

        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        
        /* Ultra soft ambient shadows loved by human designers */
        .glass-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.6);
            box-shadow: 0 4px 24px -6px rgba(15, 23, 42, 0.05), inset 0 1px 0 rgba(255,255,255,1);
        }
        
        .alert-enter { animation: alertSlide 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes alertSlide {
            from { opacity: 0; transform: translateY(10px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        
        .line-draw { animation: drawLine 1s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes drawLine {
            from { stroke-dashoffset: 200; opacity: 0; }
            to { stroke-dashoffset: 0; opacity: 1; }
        }

        /* Organic pulse for threats */
        .pulse-organic { animation: pulseOrganically 3s ease-in-out infinite; }
        @keyframes pulseOrganically {
            0%, 100% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.15); opacity: 0.4; }
        }
    </style>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useMemo, useRef } = React;

        function App() {
            const [history, setHistory] = useState([]);
            const [isLive, setIsLive] = useState(true);
            const [playbackIndex, setPlaybackIndex] = useState(0);
            const [allAlerts, setAllAlerts] = useState([]);
            const [datasetPos, setDatasetPos] = useState(0);
            const alertsEndRef = useRef(null);
            const lastAlertKey = useRef('');

            useEffect(() => {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data && data.nodes) {
                            setDatasetPos(data.dataset_position || 0);
                            setHistory(prev => {
                                const newHistory = [...prev, data];
                                if (newHistory.length > 120) newHistory.shift();
                                return newHistory;
                            });
                        }
                    } catch (err) {}
                };
                return () => ws.close();
            }, []);

            useEffect(() => {
                if (history.length === 0) return;
                const latest = history[history.length - 1];
                if (!latest || !latest.nodes) return;
                
                const newAlerts = [];
                latest.nodes.forEach(n => {
                    if (n.anomalies && n.anomalies.length > 0) {
                        const key = `${latest.timestamp}-${n.node_id}-${n.anomalies[0]}`;
                        if (key !== lastAlertKey.current) {
                            newAlerts.push({ timestamp: latest.timestamp, node_id: n.node_id, anomaly_type: n.anomalies[0] });
                            lastAlertKey.current = key;
                        }
                    }
                });
                
                if (newAlerts.length > 0) {
                    setAllAlerts(prev => {
                        const combined = [...prev, ...newAlerts];
                        if (combined.length > 40) return combined.slice(combined.length - 40);
                        return combined;
                    });
                }
            }, [history]);

            useEffect(() => {
                alertsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, [allAlerts]);

            const currentState = useMemo(() => {
                if (history.length === 0) return null;
                return isLive ? history[history.length - 1] : history[playbackIndex];
            }, [history, isLive, playbackIndex]);

            const handleSliderChange = (e) => {
                setIsLive(false);
                setPlaybackIndex(parseInt(e.target.value, 10));
            };

            const resumeLive = () => {
                setIsLive(true);
            };

            const seekDataset = async (pos) => {
                try {
                    await fetch(`/api/seek?position=${pos}`, { method: 'POST' });
                    setHistory([]);
                    setAllAlerts([]);
                    setIsLive(true);
                } catch(e) {}
            };

            if (!currentState) {
                return (
                    <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#f8fafc] text-indigo-900">
                        <div className="relative w-16 h-16 mb-6">
                            <div className="absolute inset-0 border-4 border-indigo-100 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
                        </div>
                        <div className="font-semibold tracking-[0.2em] text-xs text-slate-500 uppercase">Synchronizing Telemetry</div>
                    </div>
                );
            }

            const ACTIVE = currentState.nodes.length;
            const infectedNodes = currentState.nodes.filter(n => n.anomalies.length > 0 || n.trust_score < 80);
            const infectedCount = infectedNodes.length;
            const isUnderAttack = infectedCount > 0;
            const pZero = currentState.patient_zero;

            const uniqueNodeIds = [...new Set(currentState.nodes.map(n => n.node_id))];
            const nodePositions = {};
            const gridCols = Math.ceil(Math.sqrt(uniqueNodeIds.length));
            uniqueNodeIds.forEach((id, i) => {
                const row = Math.floor(i / gridCols);
                const col = i % gridCols;
                nodePositions[id] = {
                    x: 15 + (col * (70 / Math.max(gridCols - 1, 1))),
                    y: 15 + (row * (70 / Math.max(Math.ceil(uniqueNodeIds.length / gridCols) - 1, 1)))
                };
            });

            const datasetProgress = Math.round((datasetPos / 10000) * 100);

            // Small reusable status dot component to replace emojis
            const StatusIndicator = ({ status }) => {
                let colorClass = "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]";
                if (status === 'warning') colorClass = "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]";
                if (status === 'danger') colorClass = "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)] animate-pulse";
                if (status === 'neutral') colorClass = "bg-slate-300";
                
                return (
                    <div className="relative flex items-center justify-center w-2 h-2 mr-2">
                        <div className={`absolute inset-0 rounded-full ${colorClass}`}></div>
                        {status === 'danger' && <div className="absolute inset-[-4px] rounded-full border border-rose-400 opacity-60 pulse-organic"></div>}
                    </div>
                );
            };

            return (
                <div className="flex flex-col h-screen overflow-hidden text-slate-800 relative z-0">
                    {/* Artistic gradient mesh in the background for humanistic warmth */}
                    <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-50/60 blur-3xl -z-10 pointer-events-none"></div>
                    <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-rose-50/40 blur-3xl -z-10 pointer-events-none"></div>

                    {/* Floated Premium Nav */}
                    <header className="px-6 py-5 flex items-center justify-between shrink-0 z-10 w-full max-w-screen-2xl mx-auto">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-indigo-600 rounded-xl shadow-[0_4px_12px_rgba(79,70,229,0.3)] flex items-center justify-center text-white">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight text-slate-900 leading-tight">AEGIS Platform</h1>
                                <p className="text-[11px] font-medium text-slate-500 uppercase tracking-widest">Dataset Telemetry Engine</p>
                            </div>
                        </div>

                        {/* Top Context Indicators (Cleaner) */}
                        <div className="hidden lg:flex items-center gap-6 glass-card px-5 py-2.5 rounded-2xl border-white/80">
                            <div className="flex items-center">
                                <StatusIndicator status={isUnderAttack ? 'danger' : 'success'} />
                                <div className="flex flex-col">
                                    <span className="text-[9px] uppercase tracking-widest text-slate-400 font-semibold mb-[-2px]">Network State</span>
                                    <span className={`text-xs font-bold ${isUnderAttack ? 'text-rose-600' : 'text-slate-700'}`}>
                                        {isUnderAttack ? 'Incident Detected' : 'Operational'}
                                    </span>
                                </div>
                            </div>
                            <div className="w-px h-8 bg-slate-200"></div>
                            <div className="flex items-center">
                                <div className="flex flex-col">
                                    <span className="text-[9px] uppercase tracking-widest text-slate-400 font-semibold mb-[-2px]">Active Nodes</span>
                                    <span className="text-xs font-bold text-slate-700">{ACTIVE} Streaming</span>
                                </div>
                            </div>
                            <div className="w-px h-8 bg-slate-200"></div>
                            <div className="flex items-center">
                                <StatusIndicator status={infectedCount > 0 ? 'warning' : 'neutral'} />
                                <div className="flex flex-col">
                                    <span className="text-[9px] uppercase tracking-widest text-slate-400 font-semibold mb-[-2px]">Anomalies</span>
                                    <span className="text-xs font-bold text-slate-700">{infectedCount} Flagged</span>
                                </div>
                            </div>
                        </div>

                        {/* Controls (Soft rounded switches) */}
                        <div className="flex items-center gap-4 glass-card px-4 py-2 rounded-2xl border-white/80">
                            <button onClick={isLive ? () => setIsLive(false) : resumeLive} className="w-8 h-8 rounded-full bg-slate-100 hover:bg-white border border-slate-200 flex flex-col items-center justify-center transition shadow-sm text-indigo-600 group">
                                {isLive ? (
                                    <svg className="w-3.5 h-3.5 group-hover:scale-95 transition" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>
                                ) : (
                                    <svg className="w-4 h-4 translate-x-px group-hover:scale-110 transition" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                                )}
                            </button>
                            <div className="flex flex-col w-32">
                                <div className="flex justify-between items-center mb-1">
                                    <span className={`text-[10px] font-bold ${isLive ? 'text-indigo-600' : 'text-slate-500'}`}>
                                        {isLive ? 'LIVE STREAM' : 'DVR REPLAY'}
                                    </span>
                                    {!isLive && <span className="text-[9px] font-mono text-slate-400">T-{Math.max(0, (history.length - 1) - playbackIndex)}s</span>}
                                </div>
                                <input type="range" min={0} max={history.length > 0 ? history.length - 1 : 0}
                                    value={isLive ? history.length - 1 : playbackIndex}
                                    onChange={handleSliderChange}
                                    className="w-full accent-indigo-500 h-1 rounded-full appearance-none cursor-pointer bg-slate-200 shadow-inner overflow-hidden" />
                            </div>
                        </div>
                    </header>

                    {/* Highly aesthetic timeline bar placed organically below the header */}
                    <div className="px-8 w-full max-w-screen-2xl mx-auto mb-6 shrink-0 flex items-center justify-center gap-6">
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Dataset Scope</span>
                        <div className="flex-1 max-w-2xl h-1.5 bg-slate-200/50 rounded-full overflow-hidden shadow-inner relative flex">
                            <div className="absolute top-0 bottom-0 left-[49%] w-px bg-slate-400/50 z-10"></div>
                            <div className="absolute top-0 bottom-0 left-[75%] w-px bg-rose-400/50 z-10"></div>
                            <div className="h-full bg-gradient-to-r from-indigo-400 to-indigo-600 transition-all duration-300 rounded-full" style={{width: `${datasetProgress}%`}}></div>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => seekDataset(0)} className="text-[10px] font-semibold px-3 py-1 rounded-full bg-white text-slate-600 shadow-sm hover:shadow transition border border-slate-200/60">Reset</button>
                            <button onClick={() => seekDataset(4900)} className="text-[10px] font-semibold px-3 py-1 rounded-full bg-amber-50 text-amber-700 shadow-sm hover:shadow transition border border-amber-200/60">Schema Shift</button>
                            <button onClick={() => seekDataset(7500)} className="text-[10px] font-semibold px-3 py-1 rounded-full bg-rose-50 text-rose-700 shadow-sm hover:shadow transition border border-rose-200/60">Late Stage</button>
                        </div>
                    </div>

                    <main className="flex-1 px-6 pb-6 overflow-hidden flex flex-col gap-6 w-full max-w-screen-2xl mx-auto">
                        
                        <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
                            
                            {/* Left area: beautiful subtle threat feed */}
                            <div className="flex w-64 lg:w-[320px] flex-col gap-6 shrink-0">
                                <div className="glass-card rounded-[2rem] p-6 flex flex-col flex-1 min-h-0 relative overflow-hidden group">
                                    {/* subtle decorative blur in card */}
                                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-rose-100/50 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition duration-700"></div>

                                    <h2 className="text-[11px] font-bold tracking-[0.15em] text-slate-400 uppercase mb-4 flex items-center gap-2">
                                        <StatusIndicator status={infectedCount > 0 ? "danger" : "success"} />
                                        Threat Feed Log
                                    </h2>
                                    <div className="flex-1 overflow-y-auto pr-2 -mr-2 space-y-3 font-mono text-[10px]">
                                        {allAlerts.map((log, i) => {
                                            const typeLabel = log.anomaly_type.replace(/_/g, " ");
                                            const isIdentity = log.anomaly_type === 'IDENTITY_COMPROMISED';
                                            const isGhost = log.anomaly_type.includes('GHOST');
                                            
                                            // Soft humanistic colors for alerts instead of harsh saturated borders
                                            const colorClasses = isIdentity ? 'bg-indigo-50/80 text-indigo-900 border-indigo-200/50' : 
                                                                isGhost ? 'bg-amber-50/80 text-amber-900 border-amber-200/50' : 
                                                                'bg-rose-50/80 text-rose-900 border-rose-200/50';

                                            return (
                                                <div key={i} className={`p-3 rounded-2xl border backdrop-blur-sm shadow-sm alert-enter ${colorClasses} flex flex-col gap-1 transition-transform hover:-translate-y-0.5`}>
                                                    <div className="flex justify-between items-center opacity-70 border-b border-black/5 pb-1 mb-1">
                                                        <span className="font-semibold text-xs text-black">{typeLabel}</span>
                                                        <span>{log.timestamp.split('T')[1] || log.timestamp}</span>
                                                    </div>
                                                    <div className="flex justify-between items-end">
                                                        <span className="font-sans text-xs">Origin: <span className="font-bold">N-{log.node_id}</span></span>
                                                        <span className="text-[8px] uppercase tracking-wider font-bold bg-white/40 px-1.5 py-0.5 rounded">Action Req</span>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                        
                                        {pZero && pZero.confidence > 30 && pZero.linked_nodes && pZero.linked_nodes.length > 0 && (
                                            <div className="p-3 rounded-2xl border border-amber-300/60 bg-gradient-to-br from-amber-50 to-orange-50/80 shadow-md alert-enter flex flex-col gap-2 relative overflow-hidden">
                                                <div className="absolute top-0 right-0 w-16 h-16 bg-white/40 rounded-full blur-xl"></div>
                                                <span className="text-[9px] uppercase tracking-widest font-bold text-amber-900 flex items-center gap-2">
                                                    <svg className="w-3 h-3 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                                    Propagation Traced
                                                </span>
                                                <span className="font-mono font-medium text-amber-950 text-xs">Origin Node <span className="font-bold text-rose-600">{pZero.patient_zero_node}</span> has infected <span className="font-bold">{pZero.linked_nodes.length}</span> endpoints.</span>
                                            </div>
                                        )}
                                        <div ref={alertsEndRef} />
                                        {allAlerts.length === 0 && (
                                            <div className="h-full flex flex-col items-center justify-center text-slate-300/80 opacity-70">
                                                <svg className="w-8 h-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                                <span className="font-sans text-xs">No anomalies detected</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-1 flex-col gap-6 min-w-0">
                                <div className="flex flex-col lg:flex-row gap-6 flex-1">
                                    {/* Breathable, beautiful graph area */}
                                    <div className="flex-1 glass-card rounded-[2rem] p-6 flex flex-col relative overflow-hidden group">
                                        
                                        <div className="flex justify-between items-center z-20 pointer-events-none mb-4">
                                            <h2 className="text-[11px] font-bold tracking-[0.15em] text-slate-400 uppercase">Topology Map</h2>
                                            {pZero && pZero.confidence > 0 && <span className="bg-rose-100/80 text-rose-700 px-3 py-1 rounded-full text-[10px] uppercase tracking-widest font-bold shadow-sm backdrop-blur border border-rose-200/50">Patient Zero Identified</span>}
                                        </div>

                                        {/* Subtle background dotted pattern instead of harsh grids */}
                                        <div className="absolute inset-0 opacity-[0.2]" style={{backgroundImage: 'radial-gradient(#cbd5e1 1.5px, transparent 1.5px)', backgroundSize: '36px 36px', backgroundPosition: 'center'}}></div>

                                        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
                                            {currentState.propagation_graph && currentState.propagation_graph.map((edge, i) => {
                                                const src = nodePositions[edge.source];
                                                const tgt = nodePositions[edge.target];
                                                if (!src || !tgt) return null;
                                                return <line key={`prop-${i}`} x1={`${src.x}%`} y1={`${src.y}%`} x2={`${tgt.x}%`} y2={`${tgt.y}%`} stroke="rgba(244,63,94,0.4)" strokeWidth="1.5" strokeDasharray="4 4" className="line-draw" />
                                            })}
                                            {pZero && pZero.linked_nodes && pZero.linked_nodes.map(tid => {
                                                if (currentState.propagation_graph && currentState.propagation_graph.some(e => e.target === tid)) return null;
                                                const src = nodePositions[pZero.patient_zero_node];
                                                const tgt = nodePositions[tid];
                                                if (!src || !tgt) return null;
                                                // Softer, curved path illusion for propagation edges - bezier curves look more organic!
                                                return <path key={`p-${tid}`} d={`M ${src.x * window.innerWidth/100} ${src.y * window.innerHeight/100} Q ${50 * window.innerWidth/100} ${50 * window.innerHeight/100} ${tgt.x * window.innerWidth/100} ${tgt.y * window.innerHeight/100}`} stroke="rgba(245,158,11,0.2)" strokeWidth="1" fill="none" className="line-draw" />
                                            })}
                                        </svg>

                                        <div className="relative flex-1">
                                            {currentState.nodes.map(node => {
                                                const pos = nodePositions[node.node_id] || {x:50,y:50};
                                                const isPZ = pZero && pZero.patient_zero_node === node.node_id && pZero.confidence > 0;
                                                const isSafe = node.trust_score >= 80;
                                                
                                                // Humanized node styles - softer glows, dropping harsh borders
                                                let dotColor = 'bg-slate-300';
                                                let outerGlow = 'bg-transparent';
                                                
                                                if (isSafe && !isPZ) {
                                                    dotColor = 'bg-emerald-400';
                                                } else if (node.trust_score < 50) { 
                                                    dotColor = 'bg-rose-500'; 
                                                    outerGlow = 'bg-rose-400/20 shadow-[0_0_20px_rgba(244,63,94,0.3)] animate-pulse'; 
                                                } else if (node.trust_score < 80) { 
                                                    dotColor = 'bg-amber-400'; 
                                                    outerGlow = 'bg-amber-400/20'; 
                                                }

                                                return (
                                                    <div key={node.node_id} className={`absolute flex items-center justify-center transition-all duration-700 z-20 rounded-full ${outerGlow} ${isPZ ? 'w-10 h-10 bg-rose-500/10 shadow-[0_0_30px_rgba(244,63,94,0.4)]' : 'w-6 h-6'}`}
                                                        style={{top:`${pos.y}%`,left:`${pos.x}%`,transform:'translate(-50%,-50%)'}}>
                                                        <div className={`rounded-full transition-colors duration-500 shadow-sm ${dotColor} ${isPZ ? 'w-3.5 h-3.5 bg-rose-600' : 'w-2 h-2'}`}></div>
                                                        
                                                        {/* Extremely subtle label for non-infected, bolder for infected */}
                                                        {(!isSafe || isPZ) && (
                                                            <div className="absolute top-full mt-1.5 flex flex-col items-center">
                                                                <span className="text-[10px] font-sans text-slate-700 font-semibold whitespace-nowrap bg-white/90 px-2 py-0.5 rounded-full shadow-sm">
                                                                    {node.node_id}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>

                                    {/* Minimalist Heatmap - Tilted to look like a modern chart widget */}
                                    <div className="w-full lg:w-48 glass-card rounded-[2rem] p-5 flex flex-col items-center justify-center text-center">
                                        <h2 className="text-[11px] font-bold tracking-[0.1em] text-slate-400 uppercase mb-8">System Deviation</h2>
                                        
                                        <div className="w-full h-32 relative flex items-end justify-between px-2">
                                            {/* Baseline indicator */}
                                            <div className="absolute bottom-[20%] left-0 right-0 h-px bg-slate-200 border-b border-dashed border-slate-300 z-0"></div>
                                            
                                            {history.slice(-30).map((h, i) => {
                                                const minTrust = Math.min(...h.nodes.map(n => n.trust_score));
                                                const intensity = Math.max(0, Math.min(100, 100 - minTrust));
                                                // Softer color language
                                                let c = 'bg-emerald-300';
                                                if (intensity > 50) c = 'bg-rose-400';
                                                else if (intensity > 20) c = 'bg-amber-300';
                                                
                                                return (
                                                    <div key={i} className="w-1.5 relative group z-10 flex flex-col justify-end h-full">
                                                        <div className={`w-full rounded-full transition-all duration-300 ${c} opacity-80 group-hover:opacity-100 group-hover:scale-y-110 origin-bottom`} style={{height:`${Math.max(4,intensity)}%`}}></div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                        <span className="text-[9px] text-slate-400 mt-4 uppercase tracking-widest font-semibold">Timeline Base</span>
                                    </div>
                                </div>

                                {/* Beautiful Registry Grid */}
                                <div className="h-1/3 glass-card rounded-[2rem] flex flex-col min-h-0 relative z-30 overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                                    <div className="px-6 py-4 flex justify-between items-center z-20 border-b border-slate-100/50">
                                        <h2 className="text-[11px] font-bold tracking-[0.15em] text-slate-400 uppercase">Forensic Audit Log</h2>
                                        <button className="text-[10px] font-bold text-indigo-500 bg-indigo-50 px-3 py-1 rounded-full hover:bg-indigo-100 transition">Export CSV</button>
                                    </div>
                                    <div className="flex-1 overflow-auto rounded-b-[2rem] px-2 pb-2">
                                        <table className="w-full text-left text-xs whitespace-nowrap border-collapse">
                                            <thead className="bg-white/80 backdrop-blur sticky top-0 text-slate-400 uppercase tracking-widest text-[9px] font-bold z-10">
                                                <tr>
                                                    <th className="p-3 pl-6 font-semibold">Node</th>
                                                    <th className="p-3 font-semibold">State (Layer 1)</th>
                                                    <th className="p-3 font-semibold">HTTP (Layer 2)</th>
                                                    <th className="p-3 font-semibold">Schema (Layer 3)</th>
                                                    <th className="p-3 font-semibold">Signature</th>
                                                    <th className="p-3 font-semibold">Verdict</th>
                                                    <th className="p-3 font-semibold w-40 pr-6">Trust Vector</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100/30 text-slate-600 font-mono text-[10px]">
                                                {currentState.nodes.map(node => {
                                                    const isSafe = node.trust_score >= 80;
                                                    const isDangerous = node.trust_score < 50;
                                                    
                                                    return (
                                                        <tr key={node.node_id} className={`hover:bg-slate-50/50 transition duration-150 rounded-xl ${isDangerous ? 'bg-rose-50/20' : ''}`}>
                                                            <td className="p-3 pl-6">
                                                                <span className={`px-2 py-1 rounded-lg font-bold ${isSafe ? 'bg-indigo-50/50 text-indigo-600' : 'bg-rose-100 text-rose-700 shadow-sm'}`}>{node.node_id}</span>
                                                            </td>
                                                            <td className="p-3 font-semibold text-slate-500">{node.raw_telemetry.json_payload.status}</td>
                                                            <td className={`p-3 font-semibold ${node.raw_telemetry.http_status !== 200 ? 'text-rose-500' : 'text-slate-500'}`}>
                                                                {node.raw_telemetry.http_status} <span className="text-[9px] text-slate-400 font-normal ml-1 border border-slate-200 rounded px-1">{Math.round(node.raw_telemetry.latency*1000)}ms</span>
                                                            </td>
                                                            <td className="p-3"><span className="text-indigo-500 font-bold bg-indigo-50 px-1.5 py-0.5 rounded">{node.raw_telemetry.schema_version}</span> <span className="text-slate-400 ml-1">[{node.raw_telemetry.active_column}]</span></td>
                                                            <td className="p-3 font-medium text-slate-500 truncate max-w-[100px] hover:max-w-none text-ellipsis" title={node.decoded_identity}>{node.decoded_identity.substring(0,12)}</td>
                                                            <td className="p-3">
                                                                {(!isSafe) ? 
                                                                    <span className="flex items-center gap-1.5 text-rose-600 font-bold text-[9px] uppercase tracking-wider">
                                                                        <div className="w-1.5 h-1.5 rounded-full bg-rose-500"></div> Compromised
                                                                    </span> 
                                                                    : <span className="text-emerald-500 flex items-center gap-1.5 font-bold text-[9px] uppercase tracking-wider">
                                                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Valid
                                                                    </span>}
                                                            </td>
                                                            <td className="p-3 pr-6">
                                                                <div className="flex items-center gap-3">
                                                                    <div className="h-1 flex-1 bg-slate-100 rounded-full overflow-hidden">
                                                                        <div className={`h-full rounded-full transition-all duration-[1000ms] ease-out ${isSafe ? 'bg-emerald-400' : isDangerous ? 'bg-rose-500' : 'bg-amber-400'}`} style={{width:`${node.trust_score}%`}}></div>
                                                                    </div>
                                                                    <span className={`w-6 text-right font-bold font-sans text-xs ${isSafe ? 'text-slate-600' : 'text-rose-600'}`}>{Math.round(node.trust_score)}</span>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </main>
                </div>
            )
        }
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(top_half)

print("index.html fully humanized and rebuilt.")
