const features = [
  {
    title: 'Condition assessment',
    description:
      'Describe how your gear rides today and we will flag what needs attention before the next day on snow.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    ),
  },
  {
    title: 'Tune-up recommendations',
    description:
      'Get targeted advice on waxing, edge work, and base repair based on how many days you have ridden since your last service.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
      </svg>
    ),
  },
  {
    title: 'Local shop finder',
    description:
      'When a repair is out of DIY range, we will surface trusted ski shops within 15 miles of you on a map.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
  },
];

export default function HomePage({ onStartAssessment, onFindShop }) {
  return (
    <main className="main-container">
      <section className="home-page">
        <div className="hero">
          <span className="hero-eyebrow">Ski &amp; Snowboard Maintenance</span>
          <h1>
            Keep your gear <span>dialed in</span> all season.
          </h1>
          <p>
            Tell SkiWare about your skis or snowboard and how you have been riding.
            We will flag wear, suggest tune-ups, and point you to a nearby shop if the
            job is bigger than a garage fix.
          </p>
          <div className="hero-cta">
            <button className="btn-primary" onClick={onStartAssessment}>
              Start assessment
            </button>
            <button className="btn-secondary" onClick={onFindShop}>
              Find a shop
            </button>
          </div>
          <p className="hero-meta">Takes under two minutes · No account required</p>
        </div>

        <div className="features-grid">
          {features.map((feature) => (
            <article key={feature.title} className="feature-card">
              <div className="feature-icon" aria-hidden="true">
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
