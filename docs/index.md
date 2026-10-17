<div class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Open-source foundations · Python 3.11+</p>
    <h1>Build AI systems<br><span>you can reason about.</span></h1>
    <p class="hero-lede">
      LuckyBrain gives you small, typed building blocks for models, retrieval,
      and agents—without hiding the seams or pretending the hard parts are solved.
    </p>
    <div class="hero-actions">
      <a class="button button-primary" href="getting-started/">Get started <span aria-hidden="true">→</span></a>
      <a class="button button-secondary" href="api-reference/">Explore the API</a>
    </div>
    <p class="hero-note"><span class="status-dot"></span>Early-stage project · Clear about what works today</p>
  </div>
  <div class="code-card" aria-label="Example Python usage">
    <div class="code-card-top"><span class="window-dots"><i></i><i></i><i></i></span><span>quickstart.py</span><span class="code-language">PY</span></div>
    <pre><code><span class="code-muted">from</span> luckybrain.core.models <span class="code-muted">import</span> (
    OpenaiBrain,
)

brain = OpenaiBrain(
    model=<span class="code-string">"gpt-4o-mini"</span>,
    system_prompt=<span class="code-string">"Be clear and precise."</span>,
)

answer = brain.think(
    <span class="code-string">"Explain vector search."</span>
)
<span class="code-muted">print</span>(answer)</code></pre>
    <div class="code-card-foot"><span>Small surface area.</span><span>Real Python.</span><span>No hidden pipeline.</span></div>
  </div>
</div>

<div class="trust-strip">
  <div><strong>Provider-aware</strong><span>OpenAI and Groq clients</span></div>
  <div><strong>Composable</strong><span>Typed extension contracts</span></div>
  <div><strong>Inspectable</strong><span>Explicit boundaries and limits</span></div>
  <div><strong>Honest by design</strong><span>Alpha, with scope clearly stated</span></div>
</div>

<section class="home-section">
  <p class="eyebrow">A toolkit, not a black box</p>
  <h2>Use the pieces you need.<br><span>Keep control of the rest.</span></h2>
  <p class="section-lede">Start with the supported interfaces. Add your own providers, stores, and orchestration when your application calls for them.</p>
  <div class="feature-grid">
    <a class="feature-card" href="guides/chat-models/">
      <span class="feature-index">01 / MODELS</span>
      <h3>Talk to chat models</h3>
      <p>Use synchronous OpenAI and Groq clients with explicit prompts, options, and conversation history.</p>
      <span class="feature-link">Read the model guide <span aria-hidden="true">↗</span></span>
    </a>
    <a class="feature-card" href="guides/contracts/">
      <span class="feature-index">02 / CONTRACTS</span>
      <h3>Build against interfaces</h3>
      <p>Implement small async protocols for retrieval, reranking, generation, and agent tools.</p>
      <span class="feature-link">Explore the contracts <span aria-hidden="true">↗</span></span>
    </a>
    <a class="feature-card" href="guides/query-rewriting/">
      <span class="feature-index">03 / SEARCH</span>
      <h3>Improve a query</h3>
      <p>Optionally rewrite or expand a search query through a chat model you already provide.</p>
      <span class="feature-link">See the query guide <span aria-hidden="true">↗</span></span>
    </a>
  </div>
</section>

<section class="boundary-panel">
  <div>
    <p class="eyebrow">A useful distinction</p>
    <h2>Foundations today.<br>Room to grow tomorrow.</h2>
  </div>
  <div>
    <p>LuckyBrain is an alpha package—not a finished RAG platform. Its contracts are extension points, not built-in databases or orchestration. Open the docs to see what is implemented, how to use it, and what you still own.</p>
    <a class="text-link" href="guides/production-readiness/">Read production-readiness notes <span aria-hidden="true">→</span></a>
  </div>
</section>

<section class="home-bottom">
  <div>
    <p class="eyebrow">Build in the open</p>
    <h2>Have an idea or a better way?</h2>
    <p>Read the contribution guide, open a focused issue, or help make the interfaces clearer.</p>
  </div>
  <a class="button button-primary" href="connect/">Connect with the project <span aria-hidden="true">→</span></a>
</section>
