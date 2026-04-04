### Frontend Architectural Design

Due to the constraints of the hackathon ecosystem ensuring instantaneous execution across diverse judges and laptops, the frontend is deliberately designed utilizing **React 18** embedded directly against a standalone **Babel compiler** located inside `/frontend/index.html`. 

This eliminates the necessity of `npm install` packages breaking, conflicting versions of Node, or missing global system executables. While standard architecture logically builds features into `/components` or `/pages` using `import/export`, such modules run afoul of restrictive local file URI and CORS handling policies imposed by Chrome or Edge when avoiding bundled tools like Vite or Webpack.

For production, elements coded dynamically within `index.html` seamlessly extrapolate down into these respective directories, but for the scope of the AEGIS telemetry defense demo operations, it stands intentionally monolithic.
