// SQL condition for the "来源" filter, shared by /api/search and /api/meta.
export function sourceCond(src, col = "q.source") {
  if (src === "fresh") {
    return `(${col} LIKE '%2023%' OR ${col} LIKE '%2024%' OR ${col} LIKE '%2025%' OR ${col} LIKE '%2026%')`;
  }
  if (src === "gaokao") return `${col} LIKE '高考真题%'`;
  if (src === "mock") return `(${col} LIKE '%模拟%' OR ${col} LIKE '%联考%')`;
  return "";
}
