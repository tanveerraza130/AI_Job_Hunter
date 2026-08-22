const DISPLAY_WORDS: Record<string, string> = {
  ai: "AI",
  api: "API",
  apis: "APIs",
  b2b: "B2B",
  b2c: "B2C",
  cdp: "CDP",
  clm: "CLM",
  clv: "CLV",
  crm: "CRM",
  dlt: "DLT",
  hni: "HNI",
  ltv: "LTV",
  martech: "MarTech",
  ncr: "NCR",
  rcs: "RCS",
  seo: "SEO",
  sem: "SEM",
  sfmc: "SFMC",
  sms: "SMS",
  sql: "SQL",

  "2m": "2M",

  adobe: "Adobe",
  braze: "Braze",
  dynamics: "Dynamics",
  hubspot: "HubSpot",
  klaviyo: "Klaviyo",
  marketo: "Marketo",
  moengage: "MoEngage",
  salesforce: "Salesforce",
  tealium: "Tealium",
  webengage: "WebEngage",
};

export function formatDisplayText(
  value?: string | null,
): string {
  if (!value) {
    return "";
  }

  return value
    .trim()
    .split(/(\s+|[\/,&()\-])/g)
    .map((token) => {
      if (!token || /^\s+$/.test(token)) {
        return token;
      }

      if (/^[\/,&()\-]$/.test(token)) {
        return token;
      }

      const key = token.toLowerCase();

      if (DISPLAY_WORDS[key]) {
        return DISPLAY_WORDS[key];
      }

      if (/^\d+$/.test(token)) {
        return token;
      }

      return (
        token.charAt(0).toUpperCase() +
        token.slice(1).toLowerCase()
      );
    })
    .join("");
}
