type JobDescriptionProps = {
  paragraphs: string[];
};

export default function JobDescription({
  paragraphs,
}: JobDescriptionProps) {
  const content = paragraphs.filter(Boolean);

  return (
    <div className="job-description-body">
      <div className="job-description-points">
        {content.map((paragraph, index) => {
          const isRoleOverview =
            paragraph.trim().toLowerCase() === "role overview:";

          return (
            <div
              className={
                isRoleOverview
                  ? "job-description-point role-overview-point"
                  : "job-description-point"
              }
              key={`${index}-${paragraph.slice(0, 40)}`}
            >
              {!isRoleOverview && (
                <span
                  className="job-description-check"
                  aria-hidden="true"
                >
                  ✓
                </span>
              )}

              <p>{paragraph}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
