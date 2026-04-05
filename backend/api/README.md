### AEGIS API Routes Architectural Notice

Because AEGIS utilizes a singular global State execution loop decoupled from threaded client inputs, the core routing logic (`/api/seek/`, `/api/history`, WebSockets) remains firmly tethered to the top-level application daemon inside `main.py`.

In a dispersed micro-service environment, these functional bindings would be naturally disjointed into scalable `APIRouter` module files directly within this `/api` directory. However, to guarantee robust 5-second asynchronous tick intervals for the hackathon simulation without risking disjointed context bounds or cyclic dependencies, the routing remains monolithic in the root `main.py` controller.
