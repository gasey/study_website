# Interactive Atlas

Restored on 29 October 2026 from the owner's sibling `india-study-map/src/data/chapters`, `data/index.ts` and `types/index.ts`. The 26 chapter data files retain original educational content with import paths adjusted. They are separate from canonical exam questions and approved bank taxonomy. Original quiz arrays are retained as source data but are not rendered or scored; answer provenance review is needed before enabling them.

Public route: `/atlas`. Library → Modules & tools is its home; Library/Sections menus, homepage Study library and Geography/History/Polity/Mizoram shelves link there. Default chapter is Geography of Mizoram. Study Desk continues to mean the learner workspace.

Renderer supports the existing inline vector layers; the data test rejects unsupported raster/external layers rather than silently losing future additions. Timelines replay layer changes from chapter defaults. Layer controls, feature-name search and a keyboard-operable list accompany map gestures. Notes and features are disclosed on demand. A lazy route keeps Leaflet and chapter data out of initial question-page loading.

The legacy base administrative GeoJSON was deliberately not copied: its own source notes say it predates Telangana and Ladakh. Historical study overlays remain illustrative. OSM base tiles display the provider's data and attribution, not a separately verified official boundary layer. No offline tile download/prefetch. Browsers use normal cache/referrer behavior; tile errors expose retry and vector-only mode. Follow https://operations.osmfoundation.org/policies/tiles/ for provider usage. Leaflet API reference used: https://leafletjs.com/examples/quick-start/.

Restoration and geometry checks do not constitute a fresh fact audit of every chapter note or historical extent. Keep dates attached to inherited figures. Add new content only with source review and no claim of official MPSC scoring.
