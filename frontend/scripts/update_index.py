import re
import sys

def main():
    path = "c:/Users/anush/Downloads/rosetta (2)/rosetta/frontend/index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add ChartJS
    if "chart.js" not in content:
        content = content.replace(
            '<script src="https://d3js.org/d3.v7.min.js"></script>',
            '<script src="https://d3js.org/d3.v7.min.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
        )

    # 2. Add Component
    new_comp = """
        const ChartJsDrilldownSubgraphs = ({ node, onClose }) => {
            const { useEffect, useRef, useMemo } = React;
            
            const threatType = useMemo(() => {
                const isSleeper = node.raw_telemetry?.json_payload?.status === 'OPERATIONAL' && 
                                  ((node.raw_telemetry?.latency * 1000) > 300 || node.raw_telemetry?.http_status !== 200);
                if (isSleeper) return 'sleeper';
                if (node.trust_score < 50) return 'malware';
                if (node.trust_score < 80) return 'suspect';
                return 'clean';
            }, [node]);

            const mockData = useMemo(() => {
                const points = 60;
                const lat = []; const dev = []; const err = []; const load = []; const labels = [];
                const now = new Date();
                
                for(let i=0; i<points; i++) {
                    const t = new Date(now.getTime() - (points - 1 - i) * 10000);
                    labels.push(t.toLocaleTimeString('en-US', {hour12: false, hour: '2-digit', minute: '2-digit'}));
                    
                    if (threatType === 'sleeper') {
                        lat.push(210 + (Math.random()*2 - 1));
                        dev.push(1.0 + (Math.random()*0.1 - 0.05));
                        err.push(0 + Math.floor(Math.random()*2));
                        load.push(100);
                    } else if (threatType === 'malware') {
                        lat.push(Math.random() > 0.8 ? (800 + Math.random()*300) : (100 + Math.random()*50));
                        dev.push(Math.random() > 0.8 ? (4 + Math.random()*2) : (1 + Math.random()));
                        err.push(80 + Math.floor(Math.random()*120));
                        load.push(Math.random() > 0.8 ? 95 : 40 + Math.random()*20);
                    } else if (threatType === 'suspect') {
                        lat.push(Math.random() > 0.9 ? (300 + Math.random()*100) : (60 + Math.random()*20));
                        dev.push(Math.random() > 0.9 ? (2 + Math.random()) : (0.5 + Math.random()*0.5));
                        err.push(10 + Math.floor(Math.random()*40));
                        load.push(30 + Math.random()*15);
                    } else {
                        lat.push(30 + Math.random()*15);
                        dev.push(0.2 + Math.random()*0.3);
                        err.push(Math.random() > 0.95 ? 1 : 0);
                        load.push(15 + Math.random()*10);
                    }
                }
                return { lat, dev, err, load, labels };
            }, [threatType]);

            const latRef = useRef(null); const devRef = useRef(null); const errRef = useRef(null); const loadRef = useRef(null);
            const chartInstances = useRef([]);

            useEffect(() => {
                if (!window.Chart) return;
                chartInstances.current.forEach(c => c.destroy());
                chartInstances.current = [];

                const opts = {
                    responsive: true, maintainAspectRatio: false, animation: false,
                    plugins: { legend: { display: false }, tooltip: { enabled: false } },
                    scales: { x: { display: false }, y: { display: false, beginAtZero: true } },
                    layout: { padding: 0 }
                };

                const ctxLat = latRef.current.getContext('2d');
                chartInstances.current.push(new window.Chart(ctxLat, {
                    type: 'line', data: { labels: mockData.labels, datasets: [{ data: mockData.lat, borderColor: '#ef4444', borderWidth: 1.5, borderDash: [2, 2], pointRadius: 0, tension: 0.1 }] },
                    options: { ...opts, scales: { y: { min: 0, max: threatType==='malware'? 1200 : threatType==='sleeper'? 300 : 150, display: false }, x: { display: false } } }
                }));

                const ctxDev = devRef.current.getContext('2d');
                chartInstances.current.push(new window.Chart(ctxDev, {
                    type: 'line', data: { labels: mockData.labels, datasets: [{ data: mockData.dev, borderColor: '#3b82f6', borderWidth: 1.5, borderDash: [2, 2], pointRadius: 0, tension: 0.1 }] },
                    options: { ...opts, scales: { y: { min: 0, max: threatType==='malware'? 7 : 3, display: false }, x: { display: false } } }
                }));

                const ctxErr = errRef.current.getContext('2d');
                chartInstances.current.push(new window.Chart(ctxErr, {
                    type: 'line', data: { labels: mockData.labels, datasets: [{ data: mockData.err, borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.2)', borderWidth: 1, fill: true, pointRadius: 0, tension: 0 }] },
                    options: { ...opts, scales: { y: { min: 0, max: 200, display: false }, x: { display: false } } }
                }));

                const ctxLoad = loadRef.current.getContext('2d');
                chartInstances.current.push(new window.Chart(ctxLoad, {
                    type: 'line', data: { labels: mockData.labels, datasets: [{ data: mockData.load, borderColor: '#3b82f6', borderWidth: 1.5, borderDash: [2, 2], pointRadius: 0, tension: 0.1 }] },
                    options: { ...opts, scales: { y: { min: 0, max: 100, display: false }, x: { display: false } } }
                }));

                return () => chartInstances.current.forEach(c => c.destroy());
            }, [mockData, threatType]);

            const currentLat = mockData.lat[mockData.lat.length - 1];
            const currentDev = mockData.dev[mockData.dev.length - 1];
            const currentErr = mockData.err[mockData.err.length - 1];
            const currentLoad = mockData.load[mockData.load.length - 1];
            const avgLat = Math.round(mockData.lat.reduce((a, b) => a + b) / 60);
            const avgDev = (mockData.dev.reduce((a, b) => a + b) / 60).toFixed(2);
            
            const tStart = mockData.labels[0];
            const tEnd = mockData.labels[mockData.labels.length - 1];

            const trustColor = node.trust_score < 50 ? 'text-red-500' : node.trust_score < 80 ? 'text-orange-500' : 'text-green-500';
            let threatBadge = { label: 'CLEAN', color: 'bg-green-100 text-green-700 border-green-200' };
            let anomalySignature = 'Nominal telemetry profile';
            if (threatType === 'sleeper') { threatBadge = { label: 'SLEEPER BEACON', color: 'bg-purple-100 text-purple-700 border-purple-200' }; anomalySignature = 'Flatline latency — beacon detected'; } 
            else if (threatType === 'malware') { threatBadge = { label: 'MALWARE', color: 'bg-red-100 text-red-700 border-red-200' }; anomalySignature = 'Erratic high-latency spikes, high error rate'; } 
            else if (threatType === 'suspect') { threatBadge = { label: 'SUSPECT', color: 'bg-orange-100 text-orange-700 border-orange-200' }; anomalySignature = 'Periodic behavioral deviation'; }

            return (
                <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
                    <div className="bg-white dark:bg-slate-900 w-[500px] border-[0.5px] border-slate-300 dark:border-slate-700 shadow-2xl rounded" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-3 border-b-[0.5px] border-slate-200 dark:border-slate-800">
                            <div className="flex items-baseline gap-2">
                                <span className="font-mono text-lg font-bold text-slate-800 dark:text-slate-100">N-{node.node_id}</span>
                                <span className="font-mono text-lg font-bold text-slate-300">—</span>
                                <span className={`font-mono text-lg font-bold ${trustColor}`}>{Math.round(node.trust_score)}</span>
                                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold ml-1">trust</span>
                            </div>
                            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                            </button>
                        </div>
                        <div className="p-4">
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3" style={{fontVariant: "small-caps"}}>TEMPORAL DIAGNOSTICS (N-{node.node_id}) — 10MIN WINDOW</div>
                            <div className="space-y-1 mb-1 border-x-[0.5px] border-t-[0.5px] border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900 overflow-hidden">
                                <div className="h-[90px] relative border-b-[0.5px] border-slate-200 dark:border-slate-800">
                                    <div className="absolute top-1 left-2 text-[10px] text-slate-500" style={{fontVariantCaps: "small-caps"}}>LATENCY (MS)</div>
                                    <div className="absolute top-1 right-2 text-[10px] font-mono text-red-500">{Math.round(currentLat)}ms</div>
                                    <div className="w-full h-full pt-4 px-1 pb-1"><div className="relative w-full h-full"><canvas ref={latRef}></canvas></div></div>
                                </div>
                                <div className="h-[90px] relative border-b-[0.5px] border-slate-200 dark:border-slate-800">
                                    <div className="absolute top-1 left-2 text-[10px] text-slate-500" style={{fontVariantCaps: "small-caps"}}>DEVIATION (σ)</div>
                                    <div className="absolute top-1 right-2 text-[10px] font-mono text-blue-500">{currentDev.toFixed(1)}σ</div>
                                    <div className="w-full h-full pt-4 px-1 pb-1"><div className="relative w-full h-full"><canvas ref={devRef}></canvas></div></div>
                                </div>
                                <div className="h-[90px] relative border-b-[0.5px] border-slate-200 dark:border-slate-800">
                                    <div className="absolute top-1 left-2 text-[10px] text-slate-500" style={{fontVariantCaps: "small-caps"}}>HTTP ERRORS</div>
                                    <div className="absolute top-1 right-2 text-[10px] font-mono text-red-500">{Math.round(currentErr)}</div>
                                    <div className="w-full h-full pt-4 px-1 pb-1"><div className="relative w-full h-full"><canvas ref={errRef}></canvas></div></div>
                                </div>
                                <div className="h-[90px] relative border-b-[0.5px] border-slate-200 dark:border-slate-800">
                                    <div className="absolute top-1 left-2 text-[10px] text-slate-500" style={{fontVariantCaps: "small-caps"}}>LOAD (%)</div>
                                    <div className="absolute top-1 right-2 text-[10px] font-mono text-blue-500">{Math.round(currentLoad)}%</div>
                                    <div className="w-full h-full pt-4 px-1 pb-1"><div className="relative w-full h-full"><canvas ref={loadRef}></canvas></div></div>
                                </div>
                            </div>
                            <div className="flex justify-between items-center text-[8px] sm:text-[9px] font-mono text-slate-400 mt-1 mb-4 px-1">
                                <span>{tStart}</span><div className="h-px bg-slate-200 flex-1 mx-2"></div><span>{tEnd}</span>
                            </div>
                            <div className="border-[0.5px] border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3 flex flex-col gap-2 shadow-sm rounded-sm">
                                <div className="flex justify-between items-center text-[10px]"><span className="text-slate-500 uppercase">Endpoint Path</span><span className="font-mono text-slate-700 dark:text-slate-300">/api/v2/telemetry/{node.node_id}</span></div>
                                <div className="flex justify-between items-center text-[10px]"><span className="text-slate-500 uppercase">Zone</span><span className="font-mono text-slate-700 dark:text-slate-300">Core Network Gateway</span></div>
                                <div className="flex justify-between items-center text-[10px]"><span className="text-slate-500 uppercase">Avg Latency</span><span className="font-mono text-slate-700 dark:text-slate-300">{avgLat}ms</span></div>
                                <div className="flex justify-between items-center text-[10px]"><span className="text-slate-500 uppercase">Std Deviation</span><span className="font-mono text-slate-700 dark:text-slate-300">{avgDev}σ</span></div>
                                <div className="w-full h-[0.5px] bg-slate-200 dark:bg-slate-700 my-0.5"></div>
                                <div className="flex justify-between items-center text-[10px]"><span className="text-slate-500 uppercase">Anomaly Signature</span><span className="font-mono text-slate-700 dark:text-slate-300 max-w-[180px] text-right truncate" title={anomalySignature}>{anomalySignature}</span></div>
                                <div className="flex justify-between items-center text-[10px] mt-1"><span className="text-slate-500 uppercase">Threat Badge</span><span className={`px-2 py-0.5 border-[0.5px] rounded-[2px] font-bold text-[9px] tracking-wider uppercase shadow-sm ${threatBadge.color}`}>{threatBadge.label}</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            )
        };
"""
    
    # Let's insert the new component right before `const MultiDimensionalVisualizer`
    if "const ChartJsDrilldownSubgraphs" not in content:
        content = content.replace("const MultiDimensionalVisualizer = ({ data, onNodeSelect }) => {", new_comp + "\\n        const MultiDimensionalVisualizer = ({ data, onNodeSelect }) => {")

    # 3. Replace the entire NODE ANALYSIS OVERLAY modal
    modal_start_marker = "{/* ===== NODE ANALYSIS OVERLAY ===== */}"
    modal_end_marker = "{/* ===== PERSISTENT HISTORY MODAL ===== */}"

    if modal_start_marker in content and modal_end_marker in content:
        start_idx = content.find(modal_start_marker)
        end_idx = content.find(modal_end_marker)
        
        new_overlay = modal_start_marker + "\n                    {overlayNode && <ChartJsDrilldownSubgraphs node={overlayNode} onClose={() => setOverlayNode(null)} />}\n\n                    " + modal_end_marker
        
        content = content[:start_idx] + new_overlay + content[end_idx + len(modal_end_marker):]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
