/**
 * Navigate to a route path, handling dynamic routes for static export.
 *
 * In static export (GitHub Pages), dynamic route paths like /plans/18/
 * don't have pre-rendered HTML files. The 404.html SPA fallback doesn't
 * work with Next.js App Router because it tries to fetch RSC payloads.
 *
 * Solution: Navigate to the pre-rendered placeholder path (/plans/_/)
 * with the real ID as a query parameter. Client components read the ID
 * from the query param and use history.replaceState for a clean URL.
 */
const basePath = process.env.NODE_ENV === 'production' ? '/BOQ-2.0' : '';

export function navigateTo(path: string) {
  if (process.env.NODE_ENV === 'production') {
    // Rewrite dynamic routes to use the pre-rendered placeholder path
    const dynamicMatch = path.match(/^\/(dashboard\/(plans|projects))\/([^/]+)\/?$/);
    if (dynamicMatch) {
      const [, routeBase, , id] = dynamicMatch;
      window.location.href = `${basePath}/${routeBase}/_/?id=${id}`;
      return;
    }
  }
  window.location.href = `${basePath}${path}`;
}
