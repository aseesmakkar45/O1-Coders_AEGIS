import React, { useState, useEffect, useMemo } from 'react';
import { ShieldAlert, Activity, Pause, Play } from 'lucide-react';

function App() {
  const [history, setHistory] = useState([]); // Array of system states
  const [isLive, setIsLive] = useState(true);
  const [playbackIndex, setPlaybackIndex] = useState(0);

  useEffect(() => {
    // Connect to AEGIS backend WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.nodes) {
          setHistory(prev => {
            const newHistory = [...prev, data];
            if (newHistory.length > 60) newHistory.shift(); // Keep last 60 ticks (1 min DVR buffer)
            return newHistory;
          });
        }
      } catch (err) {
        console.error("WS Parse Error", err);
      }
    };

    return () => ws.close();
  }, []);

  // Determine which state to show (live vs replay)
  const currentState = useMemo(() => {
    if (history.length === 0) return null;
    if (isLive) return history[history.length - 1];
    return history[playbackIndex] || history[history.length - 1];
  }, [history, isLive, playbackIndex]);

  const triggerAttack = async (type) => {
    try {
      // Attack us-east as the default target demo node
      await fetch(`http://localhost:8000/api/attack/us-east/${type}`, { method: 'POST' });
    } catch(e) {
      console.error(e);
    }
  };

  const handleSliderChange = (e) => {
    setIsLive(false);
    setPlaybackIndex(Number(e.target.value));
  };

  const resumeLive = () => {
    setIsLive(true);
    setPlaybackIndex(history.length - 1);
  };

  if (!currentState) {
    return <div className="h-screen w-screen flex items-center justify-center bg-gray-950 text-emerald-500 font-mono">ESTABLISHING SECURE HANDSHAKE WITH AEGIS CORE...</div>;
  }

  // Calculate global status
  const isHealthy = currentState.nodes.every(n => n.trust_score >= 80);

  return (
    <div className="flex flex-col h-screen p-4 gap-4 bg-gray-950 overflow-hidden text-gray-200 selection:bg-emerald-500/30">
      {/* HEADER */}
      <header className="flex h-16 shrink-0 items-center justify-between rounded-lg border border-gray-800 bg-gray-900/50 px-6 shadow-sm backdrop-blur">
        <div className="flex items-center gap-3">
          <ShieldAlert className={`h-8 w-8 transition-colors ${isHealthy ? 'text-emerald-500' : 'text-red-500 animate-pulse'}`} />
          <h1 className="text-2xl font-bold tracking-wider text-gray-100">AEGIS <span className="text-gray-500">DEFENSE SYSTEM</span></h1>
        </div>
        
        <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-950 px-4 py-1.5">
          <span className="relative flex h-3 w-3">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${isHealthy ? 'bg-emerald-400' : 'bg-red-400'} opacity-75`}></span>
            <span className={`relative inline-flex h-3 w-3 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
          </span>
          <span className={`text-sm font-medium tracking-widest transition-colors ${isHealthy ? 'text-emerald-500' : 'text-red-500'}`}>
            {isHealthy ? 'SYSTEM SECURE' : 'THREAT DETECTED'}
          </span>
        </div>

        <div className="flex items-center gap-4 border-l border-gray-700 pl-6">
          <span className="text-xs font-semibold text-gray-400 tracking-widest uppercase">Attack Replay System</span>
          <div className="flex items-center gap-3">
            <button onClick={isLive ? () => setIsLive(false) : resumeLive} className="rounded p-2 text-emerald-400 hover:bg-gray-800 transition">
              {isLive ? <Pause size={18} /> : <Play size={18} />}
            </button>
            <input 
              type="range" 
              min={0} 
              max={history.length > 0 ? history.length - 1 : 0} 
              value={isLive ? history.length - 1 : playbackIndex}
              onChange={handleSliderChange}
              className="w-48 accent-emerald-500 bg-gray-800 h-2 rounded-lg appearance-none cursor-pointer" 
            />
            <span className={`text-xs font-mono font-bold ${isLive ? 'text-emerald-500 animate-pulse' : 'text-amber-500'}`}>
              {isLive ? 'LIVE' : 'DVR'}
            </span>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT GRID */}
      <div className="flex flex-1 gap-4 min-h-0">
        
        {/* SIDEBAR */}
        <div className="flex w-[350px] flex-col gap-4">
          {/* SIMULATORS CONTROLS */}
          <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4 flex flex-col gap-3">
             <h2 className="flex items-center gap-2 text-sm font-semibold tracking-wider text-gray-400 uppercase">
               <Activity size={16} /> Data Injectors
             </h2>
             <button onClick={() => triggerAttack('DDOS')} className="rounded border border-red-900/50 bg-red-950/20 px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-900/40 lg:text-left transition">Trigger DDoS Spike</button>
             <button onClick={() => triggerAttack('GHOST_NODE')} className="rounded border border-amber-900/50 bg-amber-950/20 px-4 py-2 text-sm font-medium text-amber-500 hover:bg-amber-900/40 lg:text-left transition">Trigger Ghost Node</button>
             <button onClick={() => triggerAttack('SCHEMA_ROTATION')} className="rounded border border-purple-900/50 bg-purple-950/20 px-4 py-2 text-sm font-medium text-purple-500 hover:bg-purple-900/40 lg:text-left transition">Trigger Schema Rotation</button>
             <button onClick={() => triggerAttack('IDENTITY_MASKING')} className="rounded border border-blue-900/50 bg-blue-950/20 px-4 py-2 text-sm font-medium text-blue-500 hover:bg-blue-900/40 lg:text-left transition">Trigger Identity Theft (P-Zero)</button>
          </div>

          {/* INCIDENT LOG FEED */}
          <div className="flex-1 rounded-lg border border-gray-800 bg-gray-900/50 p-4 flex flex-col min-h-0">
             <h2 className="text-sm font-semibold tracking-wider text-gray-400 uppercase mb-3 border-b border-gray-800 pb-2">Real-Time Alerts</h2>
             <div className="flex-1 overflow-y-auto font-mono text-xs flex flex-col gap-2">
               {currentState.new_logs && currentState.new_logs.slice().reverse().map((log, i) => (
                 <div key={i} className="text-red-400 bg-red-950/20 p-2 border-l-2 border-red-500 rounded-r">
                   <span className="opacity-60">[{log.timestamp}]</span> {log.anomaly_type.replace(/_/g, " ")} detected on {log.node_id}. Score: {Math.round(log.trust_score)}
                 </div>
               ))}
               {(!currentState.new_logs || currentState.new_logs.length === 0) && <div className="text-gray-500 italic">No recent anomalies detected. Listening for telemetry...</div>}
             </div>
          </div>
        </div>

        {/* CENTER BOARDS */}
        <div className="flex flex-1 flex-col gap-4 min-w-0">
           
           {/* MAP AND HEATMAP PLACEHOLDERS */}
           <div className="flex flex-col xl:flex-row gap-4 flex-1">
              
              <div className="flex-1 rounded-lg border border-gray-800 bg-gray-900/30 p-4 flex flex-col relative overflow-hidden">
                 <h2 className="text-sm font-semibold tracking-wider text-gray-400 uppercase mb-4 z-10">Forensic City Map</h2>
                 <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(#374151 1px, transparent 1px)', backgroundSize: '20px 20px'}}></div>
                 
                 <div className="relative flex-1 flex items-center justify-center">
                    {currentState.nodes.map((node, i) => {
                       const isPZ = currentState.patient_zero && currentState.patient_zero.patient_zero_node === node.node_id;
                       
                       return (
                         <div key={node.node_id} 
                              className={`absolute p-4 rounded-full flex items-center justify-center transition-all duration-300
                                 ${node.trust_score < 50 ? 'bg-red-500/20 animate-pulse border border-red-500 z-20' : 'bg-emerald-500/10 border border-emerald-500/50 z-10'}
                              `}
                              style={{
                                top: `${30 + (i * 15)}%`, left: `${15 + (i * 20)}%`
                              }}>
                            <div className={`w-4 h-4 rounded-full ${node.trust_score < 50 ? 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.8)]' : 'bg-emerald-500'}`}></div>
                            <span className="absolute -bottom-6 text-xs font-mono text-gray-300 font-bold whitespace-nowrap">
                              {node.node_id} {isPZ && '(Patient Zero)'}
                            </span>
                         </div>
                       )
                    })}
                 </div>
              </div>
              
              <div className="w-full xl:w-96 rounded-lg border border-gray-800 bg-gray-900/30 p-4 shrink-0 flex flex-col">
                 <h2 className="text-sm font-semibold tracking-wider text-gray-400 uppercase mb-2">Sleeper Heatmap</h2>
                 <span className="text-xs text-gray-500 mb-4 font-mono">Y-Axis: Deception Intensity</span>
                 
                 <div className="flex-1 flex flex-col justify-end gap-1">
                    {/* Fake Bar Chart Representation of History */}
                    <div className="flex items-end h-full gap-[2px]">
                       {history.map((h, i) => {
                          const minTrust = Math.min(...h.nodes.map(n => n.trust_score));
                          const anomalyIntensity = 100 - minTrust;
                          return (
                            <div 
                              key={i} 
                              className={`flex-1 rounded-t-sm transition-all ${anomalyIntensity > 50 ? 'bg-red-500' : 'bg-emerald-500/30'}`}
                              style={{height: `${Math.max(2, anomalyIntensity)}%`}}
                            ></div>
                          )
                       })}
                    </div>
                 </div>
              </div>
           </div>

           {/* ASSET REGISTRY TABLE */}
           <div className="h-[35%] rounded-lg border border-gray-800 bg-gray-900/50 p-4 shrink-0 flex flex-col min-h-0 relative z-20 shadow-lg">
             <div className="flex justify-between items-center mb-3 border-b border-gray-800 pb-2">
                 <h2 className="text-sm font-semibold tracking-wider text-gray-400 uppercase">Live Asset Registry</h2>
                 {currentState.patient_zero && currentState.patient_zero.confidence > 0 && (
                     <div className="text-xs font-mono font-bold bg-amber-500/20 text-amber-500 px-3 py-1 rounded border border-amber-500/30 animate-pulse">
                         PATIENT ZERO IDENTIFIED: {currentState.patient_zero.patient_zero_node} (CONFIDENCE: {currentState.patient_zero.confidence}%)
                     </div>
                 )}
             </div>
             <div className="flex-1 overflow-auto rounded border border-gray-800 bg-gray-950">
               <table className="w-full text-left text-xs whitespace-nowrap">
                 <thead className="bg-gray-900 sticky top-0 text-gray-400 uppercase tracking-wide">
                   <tr>
                     <th className="p-3 font-semibold">Node ID</th>
                     <th className="p-3 font-semibold">JSON Metric (L1)</th>
                     <th className="p-3 font-semibold">HTTP Layer (L2)</th>
                     <th className="p-3 font-semibold">Decoded ID (L4)</th>
                     <th className="p-3 font-semibold">Last Anomaly</th>
                     <th className="p-3 font-semibold w-64">Trust Score (0-100)</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-gray-800 font-mono text-gray-300">
                    {currentState.nodes.map((node) => {
                       const L1 = node.raw_telemetry.json_payload.status;
                       const L2 = `${node.raw_telemetry.http_status} (${Math.round(node.raw_telemetry.latency * 1000)}ms)`;
                       const L4 = node.decoded_identity;
                       const isSafe = node.trust_score >= 80;
                       
                       return (
                         <tr key={node.node_id} className="hover:bg-gray-800/50 transition-colors">
                           <td className={`p-3 font-bold ${isSafe ? 'text-emerald-400' : 'text-red-400'}`}>{node.node_id}</td>
                           <td className="p-3">{L1}</td>
                           <td className={`p-3 ${node.raw_telemetry.http_status !== 200 ? 'text-red-400' : 'text-gray-400'}`}>{L2}</td>
                           <td className={`p-3 ${L4.includes("INVALID") || !L4.includes(node.node_id) ? 'text-red-400 bg-red-950/30 font-bold' : 'text-gray-400'}`}>{L4.substring(0, 20)}{L4.length > 20 ? '...' : ''}</td>
                           <td className="p-3 text-red-400 font-bold">{node.anomalies.join(", ") || "-"}</td>
                           <td className="p-3">
                              <div className="flex items-center gap-3">
                                <div className="h-2 flex-1 bg-gray-800 rounded overflow-hidden relative">
                                  <div className={`h-full absolute left-0 top-0 transition-all duration-300 ${isSafe ? 'bg-emerald-500' : 'bg-red-500'}`} style={{width: `${node.trust_score}%`}}></div>
                                </div>
                                <span className={`w-8 text-right font-bold ${isSafe ? 'text-emerald-500' : 'text-red-500'}`}>{Math.round(node.trust_score)}</span>
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
  )
}

export default App;
