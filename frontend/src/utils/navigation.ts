/**
 * Navigate to a dynamic route path using full page navigation.
 *
 * In static export (GitHub Pages), router.push() fails for dynamic routes
 * because the RSC payload files don't exist for non-pre-rendered paths.
 * Full page navigation triggers the 404.html SPA fallback which handles routing.
 */
const basePath = process.env.NODE_ENV === 'production' ? '/BOQ-2.0' : '';

export function navigateTo(path: string) {
  window.location.href = `${basePath}${path}`;
}
