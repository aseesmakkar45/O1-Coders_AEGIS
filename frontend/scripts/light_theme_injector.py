import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace body style
html = re.sub(r'body \{ background-color: #030712; color: #f9fafb;', "body { background-color: #f8fafc; color: #0f172a;", html)
html = re.sub(r'::-webkit-scrollbar-thumb \{ background: #374151;', "::-webkit-scrollbar-thumb { background: #cbd5e1;", html)
html = re.sub(r'::-webkit-scrollbar-thumb:hover \{ background: #4B5563;', "::-webkit-scrollbar-thumb:hover { background: #94a3b8;", html)

# Replace the loader
html = html.replace('bg-gray-950 text-emerald-500', 'bg-slate-50 text-indigo-600')

# We know the return block starts around line 132.
# Instead of replacing the entire return block manually, let's write out the new layout block.
original_return = html.split('return (')[1].rsplit(')')[0]
# But there might be other parentheses. So we split by `return (` and then look for the closing `)`.
# Doing a raw text string replacement is easier. Wait, I will just write a full rewrite script.

new_return = """
                <div className="flex flex-col h-screen p-3 gap-3 bg-slate-50 overflow-hidden text-slate-800 font-sans">
                    <header className="flex h-14 shrink-0 items-center justify-between rounded-lg border border-slate-200 bg-white px-5 shadow-sm">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">🛡️</span>
                            <h1 className="text-xl font-bold tracking-tight text-slate-800 hidden sm:block">AEGIS <span className="text-slate-400 font-medium text-sm">DATASET MODE</span></h1>
                        </div>

                        <div className="flex items-center gap-3 text-[10px] font-bold tracking-widest border border-slate-200 bg-white px-3 py-1.5 rounded-lg shadow-sm">
                            <div className="flex items-center gap-1.5 pr-3 border-r border-slate-200">
                                <span className="text-slate-500">STATUS:</span>
                                <span className={`transition-colors duration-500 ${isUnderAttack ? 'text-rose-500 animate-pulse' : 'text-emerald-500'}`}>
                                    {isUnderAttack ? 'UNDER ATTACK 🔴' : 'SECURE 🟢'}
                                </span>
                            </div>
                            <div className="flex items-center gap-1.5 pr-3 border-r border-slate-200">
                                <span className="text-slate-500">P-ZERO:</span>
                                <span className={pZero && pZero.confidence > 0 ? 'text-amber-500' : 'text-emerald-500'}>
                                    {pZero && pZero.confidence > 0 ? `Node ${pZero.patient_zero_node} (${pZero.confidence}%)` : 'NONE'}
                                </span>
                            </div>
                            <div className="flex items-center gap-1.5 pr-3 border-r border-slate-200">
                                <span className="text-slate-500">ACTIVE:</span>
                                <span className="text-emerald-500">{ACTIVE}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <span className="text-slate-500">INFECTED:</span>
                                <span className={infectedCount > 0 ? 'text-rose-500' : 'text-emerald-500'}>{infectedCount}</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 border-l border-slate-200 pl-4">
                            <span className="text-[10px] font-bold text-slate-400 tracking-widest uppercase hidden lg:inline">Replay</span>
                            <button onClick={isLive ? () => setIsLive(false) : resumeLive} className="rounded border border-slate-200 p-1 text-indigo-600 hover:bg-slate-50 shadow-sm transition text-sm bg-white">
                                {isLive ? '⏸️' : '▶️'}
                            </button>
                            <input type="range" min={0} max={history.length > 0 ? history.length - 1 : 0}
                                value={isLive ? history.length - 1 : playbackIndex}
                                onChange={handleSliderChange}
                                className="w-28 lg:w-40 accent-indigo-600 h-1.5 rounded-lg appearance-none cursor-pointer bg-slate-200" />
                            <span className={`text-[10px] font-semibold ${isLive ? 'text-indigo-600 animate-pulse' : 'text-amber-500'}`}>
                                {isLive ? 'LIVE' : `DVR T-${Math.max(0, (history.length - 1) - playbackIndex)}s`}
                            </span>
                        </div>
                    </header>

                    {/* Dataset Progress Bar */}
                    <div className="flex items-center gap-3 px-2">
                        <span className="text-[10px] font-semibold text-slate-500 tracking-wider">DATASET</span>
                        <div className="flex-1 h-1.5 bg-slate-200 rounded overflow-hidden">
                            <div className="h-full bg-indigo-500 transition-all duration-300" style={{width: `${datasetProgress}%`}}></div>
                        </div>
                        <span className="text-[10px] font-semibold text-slate-500">{datasetPos}/10000</span>
                        <div className="flex gap-1">
                            <button onClick={() => seekDataset(0)} className="text-[9px] font-bold px-2 py-0.5 rounded border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 shadow-sm transition">START</button>
                            <button onClick={() => seekDataset(4900)} className="text-[9px] font-bold px-2 py-0.5 rounded border border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 shadow-sm transition">SCHEMA FLIP</button>
                            <button onClick={() => seekDataset(7500)} className="text-[9px] font-bold px-2 py-0.5 rounded border border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100 shadow-sm transition">LATE STAGE</button>
                        </div>
                    </div>

                    <div className="flex flex-1 gap-4 min-h-0">
                        {/* Left sidebar: Alerts */}
                        <div className="flex w-64 lg:w-72 flex-col gap-4">
                            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-3">
                                <h2 className="text-[10px] font-bold tracking-wider text-slate-400 uppercase mb-2">📊 Dataset Stats</h2>
                                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                                    <div className="bg-slate-50 p-2 rounded border border-slate-100">
                                        <div className="text-slate-500 font-semibold mb-1">Active Nodes</div>
                                        <div className="text-lg font-bold text-slate-700">{ACTIVE}</div>
                                    </div>
                                    <div className="bg-slate-50 p-2 rounded border border-slate-100">
                                        <div className="text-slate-500 font-semibold mb-1">Infected</div>
                                        <div className={`text-lg font-bold ${infectedCount > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>{infectedCount}</div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex-1 rounded-xl border border-slate-200 bg-white shadow-sm p-3 flex flex-col min-h-0">
                                <h2 className="text-[10px] font-bold tracking-wider text-slate-400 uppercase mb-2 border-b border-slate-100 pb-2">Real-Time Threat Feed</h2>
                                <div className="flex-1 overflow-y-auto font-mono text-[9px] lg:text-[10px] flex flex-col gap-1.5 pr-1">
                                    {allAlerts.map((log, i) => {
                                        const typeLabel = log.anomaly_type.replace(/_/g, " ");
                                        const isIdentity = log.anomaly_type === 'IDENTITY_COMPROMISED';
                                        const isGhost = log.anomaly_type.includes('GHOST');
                                        return (
                                            <div key={i} className={`p-1.5 border-l-2 rounded shadow-sm alert-enter ${isIdentity ? 'text-indigo-700 bg-indigo-50 border-indigo-400' : isGhost ? 'text-amber-700 bg-amber-50 border-amber-400' : 'text-rose-700 bg-rose-50 border-rose-400'}`}>
                                                <span className="opacity-60 font-semibold">[{log.timestamp}]</span> {typeLabel} → Node <span className="font-bold text-slate-800">{log.node_id}</span>
                                            </div>
                                        )
                                    })}
                                    {pZero && pZero.confidence > 30 && pZero.linked_nodes && pZero.linked_nodes.length > 0 && (
                                        <div className="p-1.5 border-l-2 border-amber-400 rounded shadow-sm bg-amber-50 text-amber-800 alert-enter font-bold">
                                            ⚠️ PROPAGATION: Node {pZero.patient_zero_node} → {pZero.linked_nodes.join(', ')}
                                        </div>
                                    )}
                                    <div ref={alertsEndRef} />
                                    {allAlerts.length === 0 && <div className="text-slate-400 font-sans text-xs italic">Scanning dataset...</div>}
                                </div>
                            </div>
                        </div>

                        {/* Main content */}
                        <div className="flex flex-1 flex-col gap-4 min-w-0">
                            <div className="flex flex-col lg:flex-row gap-4 flex-1">
                                {/* Forensic Map */}
                                <div className="flex-1 rounded-xl border border-slate-200 bg-white shadow-sm p-3 flex flex-col relative overflow-hidden">
                                    <h2 className="text-[10px] font-bold tracking-wider text-slate-400 uppercase mb-3 z-20 pointer-events-none">Forensic Area</h2>
                                    <div className="absolute inset-0 opacity-[0.03]" style={{backgroundImage: 'radial-gradient(#94a3b8 1px, transparent 1px)', backgroundSize: '30px 30px'}}></div>

                                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
                                        <defs>
                                            <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                                        </defs>
                                        {currentState.propagation_graph && currentState.propagation_graph.map((edge, i) => {
                                            const src = nodePositions[edge.source];
                                            const tgt = nodePositions[edge.target];
                                            if (!src || !tgt) return null;
                                            return <line key={`prop-${i}`} x1={`${src.x}%`} y1={`${src.y}%`} x2={`${tgt.x}%`} y2={`${tgt.y}%`} stroke="#f43f5e" strokeWidth="2" strokeDasharray="6 3" filter="url(#glow)" className="line-draw animate-pulse opacity-80" />
                                        })}
                                        {pZero && pZero.linked_nodes && pZero.linked_nodes.map(tid => {
                                            if (currentState.propagation_graph && currentState.propagation_graph.some(e => e.target === tid)) return null;
                                            const src = nodePositions[pZero.patient_zero_node];
                                            const tgt = nodePositions[tid];
                                            if (!src || !tgt) return null;
                                            return <line key={`p-${tid}`} x1={`${src.x}%`} y1={`${src.y}%`} x2={`${tgt.x}%`} y2={`${tgt.y}%`} stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4 4" className="line-draw opacity-50" />
                                        })}
                                    </svg>

                                    <div className="relative flex-1">
                                        {currentState.nodes.map(node => {
                                            const pos = nodePositions[node.node_id] || {x:50,y:50};
                                            const isPZ = pZero && pZero.patient_zero_node === node.node_id && pZero.confidence > 0;
                                            let dotColor = 'bg-emerald-500';
                                            let ring = 'border-slate-200 bg-white';
                                            if (node.trust_score < 50) { dotColor = 'bg-rose-500'; ring = 'border-rose-300 bg-rose-50 shadow-[0_0_15px_rgba(244,63,94,0.3)] animate-pulse'; }
                                            else if (node.trust_score < 80) { dotColor = 'bg-amber-500'; ring = 'border-amber-200 bg-amber-50'; }

                                            return (
                                                <div key={node.node_id} className={`absolute rounded-full flex items-center justify-center transition-all duration-500 z-20 border-2 ${ring} ${isPZ ? 'p-3 border-4 !border-rose-400 shadow-[0_0_25px_rgba(244,63,94,0.5)] ring-4 ring-rose-500/10' : 'p-2'}`}
                                                    style={{top:`${pos.y}%`,left:`${pos.x}%`,transform:'translate(-50%,-50%)'}}>
                                                    <div className={`rounded-full transition-colors duration-500 shadow-sm ${dotColor} ${isPZ?'w-4 h-4':'w-2 h-2'}`}></div>
                                                    <div className="absolute -bottom-8 flex flex-col items-center">
                                                        <span className="text-[9px] font-mono text-slate-700 font-bold whitespace-nowrap bg-white/90 px-1 py-0.5 rounded shadow-sm border border-slate-200">
                                                            {node.node_id}{(node.anomalies.length > 0 || node.trust_score < 80) ? <span className="text-rose-500"> ☣️</span> : ''}
                                                        </span>
                                                        {isPZ && <span className="text-[8px] font-bold text-white bg-rose-600 px-1.5 py-0.5 rounded shadow-lg animate-bounce mt-0.5 tracking-widest leading-none">P-ZERO</span>}
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>

                                {/* Heatmap */}
                                <div className="w-full lg:w-1/4 min-w-[200px] rounded-xl border border-slate-200 bg-white shadow-sm p-3 flex flex-col">
                                    <h2 className="text-[10px] font-bold tracking-wider text-slate-400 uppercase mb-1">Anomaly Heatmap</h2>
                                    <span className="text-[9px] text-slate-500 mb-3 font-mono">Trust Deviation</span>
                                    <div className="flex-1 flex flex-col justify-end">
                                        <div className="flex items-end h-[90%] gap-[1px]">
                                            {history.slice(-60).map((h, i) => {
                                                const minTrust = Math.min(...h.nodes.map(n => n.trust_score));
                                                const intensity = Math.max(0, Math.min(100, 100 - minTrust));
                                                let c = 'bg-emerald-300/80';
                                                if (intensity > 50) c = 'bg-rose-500 shadow-sm';
                                                else if (intensity > 20) c = 'bg-amber-400';
                                                return <div key={i} className={`flex-1 rounded-t-sm transition-all duration-300 ${c}`} style={{height:`${Math.max(2,intensity)}%`}}></div>
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Asset Registry */}
                            <div className="h-1/3 rounded-xl border border-slate-200 bg-white shadow-sm flex flex-col min-h-0 relative z-30">
                                <div className="px-5 py-2.5 border-b border-slate-100 bg-slate-50 rounded-t-xl flex justify-between items-center">
                                    <h2 className="text-[10px] font-bold tracking-wider text-slate-500 uppercase">Forensic Audit Log</h2>
                                </div>
                                <div className="flex-1 overflow-auto rounded-b-xl">
                                    <table className="w-full text-left text-[10px] whitespace-nowrap">
                                        <thead className="bg-slate-50 sticky top-0 text-slate-500 uppercase tracking-wider font-semibold z-10 shadow-sm border-b border-slate-100">
                                            <tr>
                                                <th className="p-2.5 px-4">Node</th>
                                                <th className="p-2.5">JSON (L1)</th>
                                                <th className="p-2.5">HTTP (L2)</th>
                                                <th className="p-2.5">Schema (L3)</th>
                                                <th className="p-2.5">Identity (L4)</th>
                                                <th className="p-2.5">Infected</th>
                                                <th className="p-2.5">Anomaly</th>
                                                <th className="p-2.5 w-36">Trust Score</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100 font-mono text-slate-600">
                                            {currentState.nodes.map(node => {
                                                const isSafe = node.trust_score >= 80;
                                                return (
                                                    <tr key={node.node_id} className={`hover:bg-slate-50 transition-colors ${node.trust_score < 50 ? 'bg-rose-50/40' : ''}`}>
                                                        <td className={`p-2.5 px-4 font-bold ${isSafe ? 'text-indigo-600' : 'text-rose-600'}`}>{node.node_id}</td>
                                                        <td className="p-2.5 font-semibold text-slate-700">{node.raw_telemetry.json_payload.status}</td>
                                                        <td className={`p-2.5 ${node.raw_telemetry.http_status !== 200 ? 'text-rose-500 font-bold' : 'text-slate-500'}`}>{node.raw_telemetry.http_status} <span className="text-[9px] text-slate-400">({Math.round(node.raw_telemetry.latency*1000)}ms)</span></td>
                                                        <td className="p-2.5 text-indigo-500 font-medium">{node.raw_telemetry.schema_version} <span className="text-slate-400">[{node.raw_telemetry.active_column}]</span></td>
                                                        <td className="p-2.5 font-medium text-slate-700">{node.decoded_identity.substring(0,12)}</td>
                                                        <td className="p-2.5">
                                                            {(node.anomalies.length > 0 || node.trust_score < 80) ? 
                                                                <span className="bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-bold text-[9px] shadow-sm tracking-wider">☣️ YES</span> 
                                                                : <span className="text-slate-400 font-bold">—</span>}
                                                        </td>
                                                        <td className={`p-2.5 font-bold ${isSafe ? 'text-slate-400' : 'text-rose-500'}`}>{node.anomalies[0]?.replace(/_/g,' ') || 'None'}</td>
                                                        <td className="p-2.5 pr-4">
                                                            <div className="flex items-center gap-2">
                                                                <div className="h-1.5 flex-1 bg-slate-200 rounded-full overflow-hidden shadow-inner">
                                                                    <div className={`h-full transition-all duration-500 ${isSafe ? 'bg-emerald-500' : node.trust_score < 50 ? 'bg-rose-500' : 'bg-amber-400'}`} style={{width:`${node.trust_score}%`}}></div>
                                                                </div>
                                                                <span className={`w-6 text-right font-bold ${isSafe ? 'text-emerald-600' : 'text-rose-600'}`}>{Math.round(node.trust_score)}</span>
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
                </div>
"""

start_idx = html.find('return (') + len('return (')
end_idx = html.rfind(')')

final_html = html[:start_idx] + new_return + html[end_idx:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Injected successfully.")
