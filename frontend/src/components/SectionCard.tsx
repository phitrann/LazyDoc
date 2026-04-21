import type { ReactNode } from "react";

type SectionCardProps = {
  id?: string;
  title: string;
  description: string;
  badges?: string[];
  action?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ id, title, description, badges = [], action, children }: SectionCardProps) {
  return (
    <section id={id} className="section-card">
      <div className="section-header">
        <div className="section-header-row">
          <h2>{title}</h2>
          <div className="section-header-meta">
            {badges.length ? (
              <div className="section-badges">
                {badges.map((badge) => (
                  <span key={badge} className="section-badge">
                    {badge}
                  </span>
                ))}
              </div>
            ) : null}
            {action}
          </div>
        </div>
        <p>{description}</p>
      </div>
      {children}
    </section>
  );
}
