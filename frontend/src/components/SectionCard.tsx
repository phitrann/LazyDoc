import type { ReactNode } from "react";

type SectionCardProps = {
  id?: string;
  title: string;
  description: string;
  badges?: string[];
  children: ReactNode;
};

export function SectionCard({ id, title, description, badges = [], children }: SectionCardProps) {
  return (
    <section id={id} className="section-card">
      <div className="section-header">
        <div className="section-header-row">
          <h2>{title}</h2>
          {badges.length ? (
            <div className="section-badges">
              {badges.map((badge) => (
                <span key={badge} className="section-badge">
                  {badge}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <p>{description}</p>
      </div>
      {children}
    </section>
  );
}
